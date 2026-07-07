"""``DjangoConnection[T]`` + ``DjangoConnectionField`` - the Relay cursor-pagination surface.

Spec: ``docs/spec-030-connection_field-0_0_9.md``.
Target release: ``0.0.9``.

Slice 1's surface (Decision 3 / Decision 4):

- ``DjangoConnection[NodeType]`` - a generic ``strawberry.relay.ListConnection``
  subclass that owns the package's ``first`` + ``last`` mutual-exclusivity
  guard (which Strawberry's ``SliceMetadata.from_arguments`` does NOT provide)
  and nothing else. It carries no ``total_count`` field.
- ``_connection_type_for(target_type)`` - resolves and caches the connection
  class for a node type: always a generated concrete ``<TypeName>Connection``
  subclass of ``DjangoConnection[target_type]``; the ``totalCount`` opt-in only
  controls whether the ``total_count`` members are added (spec-032 Slice 4 -
  a generic ALIAS handed to the schema loses the ``resolve_connection``
  override at Strawberry's generic specialization, so the bare path must be
  concrete too). The opt-in is read from ``definition.connection`` (the
  ``Meta.connection`` value stored on ``DjangoTypeDefinition``), never
  re-parsed from ``Meta``.

Slice 2's surface (Decision 5 / Decision 6 / Decision 7 / Decision 10):

- ``DjangoConnectionField(target_type, *, resolver=None, ...)`` - the PascalCase
  factory: validates the target (the four ``DjangoListField``-style guards plus
  a Relay-Node guard), synthesizes a resolver whose ``__signature__`` carries
  the ``filter`` / ``order_by`` parameters derived from the type's sidecars
  (so Strawberry's native resolver-argument derivation emits ``filter:`` /
  ``orderBy:``), and returns ``relay.connection(_connection_type_for(target_type),
  resolver=<synthesized>, ...)``.
- The synthesized resolver runs the composition pipeline
  (visibility -> filter -> orderBy -> default-order -> optimizer-plan) before
  ``ConnectionExtension`` slices the queryset, with the ``Manager`` / ``QuerySet``
  / non-queryset-iterable consumer-``resolver=`` contract.

``DjangoConnection`` and ``DjangoConnectionField`` are exported from the package
root (``django_strawberry_framework``) and dogfooded in the fakeshop example
(e.g. ``examples/fakeshop/apps/products/schema.py`` and the ``library`` app).
"""

from __future__ import annotations

import inspect
import types
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import Any, Generic, TypeVar

import strawberry
from django.db import models
from graphql import GraphQLError
from strawberry import relay
from strawberry.relay.types import NodeIterableType
from strawberry.types import Info, get_object_definition
from strawberry.types.base import StrawberryContainer
from strawberry.utils.await_maybe import AwaitableOrValue

from .list_field import _validate_relay_djangotype_target
from .optimizer.extension import apply_connection_optimization
from .optimizer.plans import (
    WINDOW_ROW_NUMBER,
    WINDOW_TOTAL_COUNT,
    deterministic_order,
    ends_in_unique_column,
)
from .optimizer.selections import direct_child_selected, named_children, prime_selected_fields
from .optimizer.walker import _relation_connection_to_attr
from .types.resolvers import _check_n1
from .utils.connections import (
    CONNECTION_FILTER_KWARG,
    CONNECTION_ORDER_KWARG,
    connection_sidecar_inputs_from_kwargs,
    derive_connection_window_bounds,
    has_connection_sidecar_input,
)
from .utils.querysets import (
    apply_type_visibility_async,
    apply_type_visibility_sync,
    initial_queryset,
    model_for,
    normalize_query_source,
)
from .utils.typing import is_async_callable

# Re-export the hoisted deterministic-order predicate under its original
# private name so the spec-030 ``tests/test_connection.py`` pins keep importing
# ``_ends_in_unique_column`` from here unchanged. The canonical implementation
# now lives in ``optimizer/plans.py`` (spec-033 Decision 11, the cursor-parity
# invariant - one source for plan-time and resolve-time order).
_ends_in_unique_column = ends_in_unique_column

NodeType = TypeVar("NodeType")

# Field name carried on the connection instance for the captured ``totalCount``;
# ``None`` (the default) means the count was not requested / not run, which the
# ``total_count`` field resolver returns verbatim per the selection-gating
# contract (Decision 4).
_TOTAL_COUNT_ATTR = "_django_total_count"

# Sentinel distinguishing "nodes is not a windowed wrapper" (so the caller
# delegates to the shipped slicing path) from a built connection a caller must
# return as-is. A module-level object so the identity check is unambiguous and
# can never collide with a legitimate ``resolve_connection`` return.
_NOT_A_WINDOW: Any = object()


@dataclass
class _WindowedConnectionRows:
    """Internal marker handing windowed prefetch rows to ``resolve_connection``.

    The synthesized relation-connection resolver (Decision 5) returns this in
    place of the per-parent node iterable when the walker's windowed prefetch
    fired: ``rows`` is the ``_dst_<field>_connection`` ``to_attr`` list of
    annotated model instances (each carrying ``_dst_row_number`` /
    ``_dst_total_count``), and ``fallback`` re-runs the shipped per-parent
    pipeline for the ambiguous-empty windows the resolver cannot classify
    (``first: 0`` / overshot ``after:``) - the resolver lacks the pagination
    arguments needed to tell genuine-empty from ambiguous-empty (Strawberry's
    ``ConnectionExtension.resolve`` consumes ``first`` / ``last`` / ``before`` /
    ``after`` and never forwards them to the resolver, only to
    ``resolve_connection``), so the slice classification happens in
    ``resolve_connection``, which falls back via this callable when needed.

    NOT a connection instance and NOT exported (no public symbol - spec
    "adds no public symbol"); the ``resolve_connection`` paths
    ``isinstance``-detect it after the ``first`` + ``last`` guard.
    """

    rows: list[Any]
    fallback: Callable[[], Any] = dataclass_field(repr=False)


def _build_windowed_fallback(target_type: type, source: Any, info: Info) -> Callable[[], Any]:
    """Return a zero-arg callable re-running the per-parent pipeline.

    Carried on ``_WindowedConnectionRows`` so ``resolve_connection`` can recover
    the shipped per-parent queryset for an ambiguous-empty window without the
    walker's slice helper or the live relation manager (which the resolver,
    not ``resolve_connection``, holds). ``source`` is the same
    ``getattr(root, accessor).all()`` value the fallback path consumes; no
    sidecar input reaches the fast path (the resolver refuses the window when
    ``filter`` / ``order_by`` kwargs are present), so the fallback runs the
    pipeline with empty sidecars.
    """
    return lambda: _pipeline_sync(
        target_type,
        source,
        info,
        filter_input=None,
        order_by_input=None,
    )


def _window_edge_class(cls: type) -> Any:
    """Resolve the connection's edge class exactly as ``ListConnection`` does.

    ``get_object_definition`` -> ``edges`` field -> ``resolve_type`` -> unwrap
    the ``StrawberryContainer`` (``list[Edge[Node]]``) down to the concrete
    ``Edge`` subclass, so the fast path builds edges through Strawberry's own
    edge type (cursor PREFIX + base64 stay owned there - the fast path passes
    only the integer offset).
    """
    type_def = get_object_definition(cls, strict=True)
    field_def = type_def.get_field("edges")
    edge_type = field_def.resolve_type(type_definition=type_def)
    while isinstance(edge_type, StrawberryContainer):
        edge_type = edge_type.of_type
    return edge_type


def _resolve_from_window(
    cls: type,
    window: _WindowedConnectionRows,
    *,
    info: Info,
    offset: int,
    limit: int | None,
    reverse: bool = False,
    want_count: bool,
    **kwargs: Any,
) -> Any:
    """Build the Relay connection straight from the windowed prefetch rows.

    The single edge / cursor / ``pageInfo`` / ``totalCount`` derivation shared
    by both ``resolve_connection`` paths (Decision 5).

    The historically-ambiguous empty shapes (``offset > 0`` overshot ``after:``,
    ``limit == 0`` ``first: 0``) are served from MARKER rows (connection window
    rigor, workstream C): ``apply_window_pagination`` keeps each partition's
    row 1 for these shapes, so an empty rows list now PROVES the parent has no
    children (serve the zero page), and a marker-only list carries the real
    ``_dst_total_count`` (serve the empty page with true count/flags). Markers
    (row 1 when ``offset > 0``; every row when ``limit == 0``) are excluded
    from edge building, so cursors are untouched. Page flags for the served
    empty pages replicate Strawberry's ``ListConnection`` arithmetic exactly
    (``has_previous_page = offset > 0`` even for a childless parent - the
    pipeline computes ``start > 0`` before looking at the data;
    ``has_next_page = total > offset``, the "would the overfetch have yielded
    a row" predicate) - byte parity with the per-parent pipeline is the bar.

    Returns ``None`` to tell the caller the window cannot be served and must
    fall back to the per-parent pipeline: a reversed ``last: 0`` window
    (upstream's ``edges[-0:]`` quirk serves ALL edges - only the pipeline
    reproduces it), or a count-less window whose selection requests a
    count-derived field (the workstream-B defensive tail - see the ``total``
    read below).

    Cursor math is the positional offset cursor ``_dst_row_number - 1`` for
    EVERY window, including the ``last``-only reversed one: Slice 1's
    ``apply_window_pagination`` keeps ``_dst_row_number`` as the FORWARD row
    number and uses a separate ``_dst_row_number_reversed`` only for the
    plan-time ``__lte`` row filter, so the rows arrive in forward order with
    forward row numbers (``[d, e]`` numbered ``4, 5`` for ``last: 2`` of five
    rows). The forward absolute-offset cursor therefore matches the pipeline's
    ``ListConnection`` cursors directly - no ``_dst_total_count - row_number``
    re-derivation (that is the scheme an earlier spec revision described;
    neither upstream ``strawberry-django`` nor Slice 1's port overwrites the
    forward row number - both keep it forward and use a separate reversed
    annotation only for the plan-time ``__lte`` filter). The cursor
    PREFIX / base64 stay owned by the edge class - the fast path passes only the
    integer offset.
    """
    rows = window.rows
    if not rows:
        if reverse and limit == 0:
            # ``last: 0``: upstream ``ListConnection`` slices ``edges[-0:]``,
            # which is the WHOLE list - only the per-parent pipeline reproduces
            # that quirk, so the (always-empty) reversed window falls back.
            return None
        # With marker rows planned for the ambiguous shapes (workstream C), an
        # empty forward window now PROVES the parent has no related rows for
        # EVERY shape - a parent with children would have kept its row 1. Page
        # flags replicate the pipeline: ``has_previous_page = offset > 0``
        # (``ListConnection`` computes ``start > 0`` before looking at the
        # data), ``has_next_page`` False (no row survived the overfetch probe).
        conn = cls(
            edges=[],
            page_info=relay.PageInfo(
                start_cursor=None,
                end_cursor=None,
                has_previous_page=offset > 0,
                has_next_page=False,
            ),
        )
        if want_count:
            setattr(conn, _TOTAL_COUNT_ATTR, 0)
        return conn

    # Marker exclusion (workstream C): for the ambiguous shapes the window
    # keeps each partition's row 1 as a marker alongside the page rows. The
    # page proper is the rows past the offset (``limit == 0`` has no page at
    # all); a marker that IS a page row is impossible (page rows have
    # ``row_number > offset >= 1``). Reversed windows never plan markers.
    ambiguous = not reverse and (offset > 0 or limit == 0)
    if ambiguous:
        page_rows = (
            [] if limit == 0 else [row for row in rows if getattr(row, WINDOW_ROW_NUMBER) > offset]
        )
    else:
        page_rows = rows
    if not page_rows:
        # Marker-only window: children exist (the marker is one) but the page
        # is empty. Serve the true count and the pipeline's flag arithmetic:
        # ``has_previous_page = offset > 0`` (``start > 0``);
        # ``has_next_page = total > offset`` (the overfetch probe - for
        # ``first: 0`` a row exists past the offset; for an overshot ``after:``
        # ``total <= offset`` by construction, so it is False).
        total = getattr(rows[-1], WINDOW_TOTAL_COUNT, None)
        if total is None:
            return None  # workstream-B drift guard: never infer a count.
        conn = cls(
            edges=[],
            page_info=relay.PageInfo(
                start_cursor=None,
                end_cursor=None,
                has_previous_page=offset > 0,
                has_next_page=total > offset,
            ),
        )
        if want_count:
            setattr(conn, _TOTAL_COUNT_ATTR, total)
        return conn
    # The count is annotated CONDITIONALLY (workstream B): the walker plans it
    # only when the selection can observe it (``totalCount`` /
    # ``pageInfo.hasNextPage``) or the window shape needs it. A count-less row
    # with either observer requested means the plan-time predicate and this
    # resolve-time read have DRIFTED (they share the selection walk in
    # ``optimizer/selections.py``, so by construction this is unreachable
    # until they diverge) - fall back per-parent rather than serve a wrong
    # flag/count, checked BEFORE any edge is built so the fallback discards no
    # work. Without an observer, the missing count is inert: the
    # ``has_next_page=False`` below is a placeholder that is never serialized.
    last_row = page_rows[-1]
    total = getattr(last_row, WINDOW_TOTAL_COUNT, None)
    if total is None and (want_count or _has_next_page_requested(info)):
        return None
    edge_class = _window_edge_class(cls)
    edges = [
        edge_class.resolve_edge(
            cls.resolve_node(node, info=info, **kwargs),
            cursor=getattr(node, WINDOW_ROW_NUMBER) - 1,
        )
        for node in page_rows
    ]
    # Row numbers are forward and the rows are forward-ordered, so the page
    # flags are the upstream forward-window comparisons against the partition's
    # total count (``resolve_optimized_connection_by_prefetch``): a previous page
    # exists when the first row is past row 1; a next page exists when the last
    # row is short of the total. These hold for the reversed ``last``-only window
    # too because its row numbers stay forward (``last: 2`` of 5 -> rows 4, 5 ->
    # hasPrevious True, hasNext False - matching the pipeline).
    first_rn = getattr(page_rows[0], WINDOW_ROW_NUMBER)
    conn = cls(
        edges=edges,
        page_info=relay.PageInfo(
            start_cursor=edges[0].cursor,
            end_cursor=edges[-1].cursor,
            has_previous_page=first_rn > 1,
            has_next_page=(
                False if total is None else getattr(last_row, WINDOW_ROW_NUMBER) < total
            ),
        ),
    )
    if want_count:
        setattr(conn, _TOTAL_COUNT_ATTR, total)
    return conn


def _consume_window(
    cls: type,
    nodes: Any,
    *,
    info: Info,
    before: str | None,
    after: str | None,
    first: int | None,
    last: int | None,
    max_results: int | None,
    want_count: bool,
    **kwargs: Any,
) -> Any:
    """Detect the windowed-row wrapper and either fast-path it or fall back.

    Shared entry from both ``resolve_connection`` paths. Computes the slice
    ``(offset, limit, reverse)`` from the pagination arguments
    ``resolve_connection`` receives (the resolver never sees them) using the
    same ``SliceMetadata`` engine and ``relay_max_results`` cap the walker used,
    so the resolve-time window matches the plan-time window by construction (the
    cursor-parity invariant's resolve-time half, Decision 4 / Decision 5). When
    the window is consumable, builds the Relay object via ``_resolve_from_window``;
    when it is an ambiguous-empty window, runs the wrapper's carried per-parent
    fallback so ``first: 0`` / overshot ``after:`` stay byte-identical. Returns
    a sentinel string ``"__not_a_window__"`` when ``nodes`` is not a wrapper, so
    the caller delegates to the shipped path.
    """
    if not isinstance(nodes, _WindowedConnectionRows):
        return _NOT_A_WINDOW
    # Derive the window through the SHARED contract the walker planned with
    # (``utils/connections.py::derive_connection_window_bounds``), so the
    # resolve-time window matches the plan-time one by construction (the
    # cursor-parity invariant). Resolver arguments are already coerced by
    # Strawberry, so any malformed-pagination ``ValueError`` / ``TypeError``
    # propagates as the field's own error (the walker, by contrast, catches it to
    # leave the selection unplanned).
    bounds = derive_connection_window_bounds(
        info,
        before=before,
        after=after,
        first=first,
        last=last,
        max_results=max_results,
    )
    built = _resolve_from_window(
        cls,
        nodes,
        info=info,
        offset=bounds.offset,
        limit=bounds.limit,
        reverse=bounds.reverse,
        want_count=want_count,
        **kwargs,
    )
    if built is not None:
        return built
    # Unservable window (reversed ``last: 0`` quirk, or the workstream-B drift
    # guard): recover the per-parent queryset and run the shipped pipeline so
    # the results stay byte-identical.
    return _consume_fallback(
        cls,
        nodes.fallback(),
        info=info,
        before=before,
        after=after,
        first=first,
        last=last,
        max_results=max_results,
        want_count=want_count,
        **kwargs,
    )


def _consume_fallback(
    cls: type,
    nodes: Any,
    *,
    info: Info,
    want_count: bool,
    **slice_kwargs: Any,
) -> Any:
    """Run the shipped per-parent path over a recovered queryset.

    The ambiguous-empty fallback tail: ``DjangoConnection.resolve_connection``
    (which ``super()`` reaches) does the ``first`` + ``last`` guard and slicing;
    the ``totalCount`` variant additionally attaches the count. Reuses the
    inherited ``ListConnection`` slicing - no second slice implementation.
    """
    conn = super(DjangoConnection, cls).resolve_connection(nodes, info=info, **slice_kwargs)
    if inspect.isawaitable(conn):
        return _attach_count_async(conn, nodes, want_count=want_count)
    return _attach_count_sync(conn, nodes, want_count=want_count)


def _guard_first_and_last(first: int | None, last: int | None) -> None:
    """Raise ``GraphQLError`` when both ``first`` and ``last`` are supplied.

    The package's own pagination guard (Decision 3): Strawberry's
    ``SliceMetadata.from_arguments`` applies ``first`` then ``last`` without a
    mutual-exclusivity check, so the package enforces it here - a query-runtime
    error landing in the GraphQL ``errors`` array, NOT a construction-time
    ``ConfigurationError``. Single-sited so the literal lives once and both the
    base and the generated ``<TypeName>Connection`` reuse it.
    """
    if first is not None and last is not None:
        raise GraphQLError(
            "Connection arguments `first` and `last` are mutually exclusive; supply only one.",
        )


def _total_count_requested(info: Info) -> bool:
    """Return whether the query selects the connection's ``totalCount`` field.

    Checks the connection field's DIRECT children (``totalCount`` is a sibling
    of ``edges`` / ``pageInfo``); the GraphQL field name is camelCase
    ``totalCount`` regardless of the Python ``total_count`` attribute.

    Scoped to the direct children deliberately: unlike
    strawberry-django's ``_should_optimize_total_count``, which recurses through
    the WHOLE ``edges { node { ... } }`` subtree, this recurses only THROUGH
    fragment wrappers (so a fragment-wrapped ``totalCount`` at the connection
    level still counts) and does NOT descend into a regular field's selections.
    Once nested connections land (WIP-032/033), a node-level ``totalCount`` deep
    inside ``edges { node { ... } }`` must not make the OUTER connection's
    predicate fire (a spurious ``COUNT`` and, on a non-queryset source, a
    spurious M1-guard raise).

    Delegates the "direct child through fragment wrappers only" walk to the
    shared ``optimizer/selections.py::direct_child_selected`` (the 0.0.9 DRY
    pass, ``docs/feedback.md`` Major 2) so the count-detection's
    fragment-descent rule cannot drift from the optimizer's selection planning.
    """
    return any(
        direct_child_selected(selected_field.selections, "totalCount")
        for selected_field in info.selected_fields
    )


def _has_next_page_requested(info: Info) -> bool:
    """Return whether the query selects ``pageInfo { hasNextPage }``.

    The ``hasNextPage`` sibling of ``_total_count_requested``: the window fast
    path derives ``hasNextPage`` from the partition's ``_dst_total_count``
    (``row_number < total``), and workstream B makes that annotation
    conditional - so when a window arrives WITHOUT the count,
    ``_resolve_from_window`` consults this predicate to decide whether the
    missing annotation is observable (defensive per-parent fallback) or inert
    (placeholder flag, never serialized). Same walk discipline as the
    plan-time ``optimizer/selections.py::connection_count_required``: direct
    ``pageInfo`` children through fragment wrappers only, then a direct
    ``hasNextPage`` under each - sharing ``named_children`` /
    ``direct_child_selected`` so the two halves cannot drift independently.
    """
    return any(
        direct_child_selected(getattr(page_info, "selections", None) or [], "hasNextPage")
        for selected_field in info.selected_fields
        for page_info in named_children(selected_field, "pageInfo")
    )


def _resolve_connection_fast_path(
    cls: type,
    nodes: Any,
    *,
    info: Info,
    want_count: bool | Callable[[], bool],
    before: str | None,
    after: str | None,
    first: int | None,
    last: int | None,
    max_results: int | None,
    **kwargs: Any,
) -> tuple[Any, bool]:
    """Run the shared ``resolve_connection`` head: the guard, then the windowed fast path.

    Both ``DjangoConnection.resolve_connection`` and the ``totalCount`` variant
    generated by ``_build_total_count_connection`` open with the same skeleton
    (the 0.0.9 DRY pass, ``docs/feedback.md`` "Connection Resolve-Connection
    Wrapper"): the Decision-3 ``first`` + ``last`` mutual-exclusivity guard, then
    the Decision-5 ``_WindowedConnectionRows`` detection that builds the Relay
    object straight from the windowed-prefetch ``_dst_row_number`` /
    ``_dst_total_count`` annotations (or runs the ambiguous-empty per-parent
    fallback the wrapper carries).

    ``want_count`` may be a bool or a zero-arg callable. A callable is evaluated
    AFTER the guard, so the ``totalCount`` variant's count-selection inspection
    (``_total_count_requested(info)``) never touches ``info`` when ``first`` +
    ``last`` are both supplied - the guard's ``GraphQLError`` short-circuits
    first (pinned by ``test_first_and_last_guard_on_generated_subclass``, which
    passes a minimal ``info``). The resolved flag is threaded into the window
    builder so a windowed ``totalCount`` is read from the annotation rather than
    counted.

    Returns ``(built_or_NOT_A_WINDOW, resolved_want_count)``: the built
    connection when the fast path fired, else ``_NOT_A_WINDOW`` so the caller
    delegates to its own ``ListConnection`` ``super().resolve_connection`` path.
    Count SELECTION and the non-window count ATTACHMENT (``_attach_count_*``)
    stay explicit in the ``totalCount`` variant, per the review.
    """
    _guard_first_and_last(first, last)
    # Seed ``info.selected_fields`` with the package's anonymous-inline-fragment-safe
    # conversion BEFORE either the ``want_count`` lambda (``_total_count_requested``)
    # or Strawberry's own ``ListConnection.resolve_connection`` reads it. Both reach
    # the same crashing ``convert_selections`` via the cached property; priming the
    # cache once here routes every later read through the package's safe adapter.
    # Runs AFTER the guard so a ``first`` + ``last`` error still short-circuits
    # before ``info`` is touched (``test_first_and_last_guard_on_generated_subclass``).
    prime_selected_fields(info)
    resolved_want_count = want_count() if callable(want_count) else want_count
    built = _consume_window(
        cls,
        nodes,
        info=info,
        before=before,
        after=after,
        first=first,
        last=last,
        max_results=max_results,
        want_count=resolved_want_count,
        **kwargs,
    )
    return built, resolved_want_count


class DjangoConnection(relay.ListConnection[NodeType], Generic[NodeType]):
    """Generic Relay connection base owning the ``first`` + ``last`` guard.

    Subclasses ``strawberry.relay.ListConnection`` so Strawberry owns cursor
    encoding, ``pageInfo``, edge wrapping, and the slice window. The only
    behavior this base adds is the Decision 3 ``first`` + ``last`` guard in the
    ``resolve_connection`` override; it carries no ``total_count`` field (that
    is the opt-in ``<TypeName>Connection`` variant's job, Decision 4).
    """

    @classmethod
    def resolve_connection(
        cls,
        nodes: NodeIterableType[NodeType],
        *,
        info: Info,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        max_results: int | None = None,
        **kwargs: Any,
    ) -> AwaitableOrValue[Any]:
        """Apply the ``first`` + ``last`` guard, then delegate to ``ListConnection``.

        The fast path (Decision 5): after the guard and before Strawberry's list
        slicing, detect the internal ``_WindowedConnectionRows`` wrapper the
        synthesized relation-connection resolver returns when the walker's
        windowed prefetch fired, and build the Relay object straight from the
        ``_dst_row_number`` / ``_dst_total_count`` annotations - one window query
        for every parent's page, zero per-parent queries. ``nodes`` that is not
        a wrapper (no optimizer, a fallback shape, a consumer prefetch) falls
        through to the shipped ``ListConnection`` path unchanged, so correctness
        never depends on the plan having fired. The through-schema test is
        mandatory because ``ConnectionExtension.resolve`` wraps the resolver.
        """
        built, _want_count = _resolve_connection_fast_path(
            cls,
            nodes,
            info=info,
            want_count=False,
            before=before,
            after=after,
            first=first,
            last=last,
            max_results=max_results,
            **kwargs,
        )
        if built is not _NOT_A_WINDOW:
            return built
        return super().resolve_connection(
            nodes,
            info=info,
            before=before,
            after=after,
            first=first,
            last=last,
            max_results=max_results,
            **kwargs,
        )


_connection_type_cache: dict[type, type] = {}


def clear_connection_type_cache() -> None:
    """Clear the per-target generated-connection-class cache.

    Test-only - production never reloads the schema. Wired into
    ``registry.clear()`` (the documented registry reset) so a registry-clearing
    test or fixture also drops the generated ``<TypeName>Connection`` classes,
    rather than accumulating dead identity-keyed entries across schema reloads.
    The cache is keyed on ``target_type`` identity,
    so a stale entry is never *wrong* - this clear is hygiene, not correctness.
    """
    _connection_type_cache.clear()


def _generate_connection_class(
    target_type: type,
    populate: Callable[[dict], None] | None = None,
    *,
    description: str | None = None,
) -> type:
    """Generate a concrete ``<TypeName>Connection`` subclass of ``DjangoConnection[target_type]``.

    The single-sited generation tail shared by both ``_connection_type_for``
    branches: ``populate`` (when given) fills the class namespace (the
    ``totalCount`` variant's members); ``description`` is forwarded to
    ``strawberry.type`` (the bare variant preserves the parent's inherited SDL
    description; the opted variant ships description-less, today's SDL shape).

    Name the generated connection from the node type's canonical GraphQL type
    name (``graphql_type_name`` - ``Meta.name`` when set, else the Python
    ``__name__``), NOT the raw Python ``__name__``. Two DjangoType classes may
    share a Python ``__name__`` while declaring distinct ``Meta.name`` values;
    naming from ``__name__`` would generate two connection classes with the
    SAME SDL type name, which Strawberry collapses into one - cross-wiring the
    two fields' ``edges`` / node types.
    ``graphql_type_name`` is the same surface-name source the finalizer and the
    filter / order input types derive from.
    """
    definition = target_type.__django_strawberry_definition__
    generated = types.new_class(
        f"{definition.graphql_type_name}Connection",
        (DjangoConnection[target_type],),
        exec_body=populate,
    )
    return strawberry.type(generated, description=description)


def _build_total_count_connection(target_type: type) -> type:
    """Generate the concrete ``<TypeName>Connection`` carrying ``totalCount``.

    The generated class subclasses ``DjangoConnection[target_type]`` (so it
    inherits the ``first`` + ``last`` guard), declares a ``total_count`` field
    whose resolver reads a private instance attribute, and overrides
    ``resolve_connection`` to count the post-filter pre-slice ``nodes``
    queryset (sync ``.count()`` / async ``.acount()``) ONLY when ``totalCount``
    is in the selection set, attach the count to the connection instance, then
    delegate to super for slicing (Decision 4).
    """

    @strawberry.field(description="Total number of nodes in the connection.")
    def total_count(self: Any) -> int:
        # The field renders ``Int!`` (the ``__annotations__`` below win for the
        # SDL); ``-> int`` is the honest return type because the count path is
        # QuerySet-only (the connection field's M1 rule raises a ``GraphQLError``
        # before a non-queryset return can reach ``totalCount``). The attribute
        # is always set by ``resolve_connection`` when the field is selected
        # over a queryset source.
        return getattr(self, _TOTAL_COUNT_ATTR)

    @classmethod
    def resolve_connection(
        cls: type,
        nodes: NodeIterableType[NodeType],
        *,
        info: Info,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        max_results: int | None = None,
        **kwargs: Any,
    ) -> AwaitableOrValue[Any]:
        # The shared ``_resolve_connection_fast_path`` runs the ``first`` +
        # ``last`` guard FIRST, then evaluates the ``want_count`` lambda
        # (count-selection inspection runs only AFTER the guard, so a first+last
        # error short-circuits before ``info`` is touched), then the windowed
        # fast path. That fast path branches on the wrapper BEFORE the count work
        # so the ``_WindowedConnectionRows`` marker - which is NOT a queryset - is
        # treated as an annotated optimized source: ``totalCount`` is read from
        # ``_dst_total_count`` on any annotated row inside ``_resolve_from_window``
        # rather than counted, bypassing ``_guard_total_count_countable`` /
        # ``.count()`` entirely (Decision 5). Ambiguous empty wrappers
        # (``limit == 0`` / ``offset > 0``) fall back to the per-parent pipeline,
        # which counts correctly, preserving the shipped totalCount / pageInfo
        # contract. Pins:
        # ``test_fast_path_total_count_marker_bypasses_non_queryset_guard`` /
        # ``test_fast_path_first_zero_falls_back_for_total_count_and_pageinfo``.
        built, want_count = _resolve_connection_fast_path(
            cls,
            nodes,
            info=info,
            want_count=lambda: _total_count_requested(info),
            before=before,
            after=after,
            first=first,
            last=last,
            max_results=max_results,
            **kwargs,
        )
        if built is not _NOT_A_WINDOW:
            return built
        # Not a window: delegate to super (the inherited guard + slicing) then
        # attach the per-parent count, the shipped totalCount path unchanged.
        conn = super(generated, cls).resolve_connection(
            nodes,
            info=info,
            before=before,
            after=after,
            first=first,
            last=last,
            max_results=max_results,
            **kwargs,
        )
        if inspect.isawaitable(conn):
            return _attach_count_async(conn, nodes, want_count=want_count)
        return _attach_count_sync(conn, nodes, want_count=want_count)

    def _populate(namespace: dict) -> None:
        namespace["__annotations__"] = {"total_count": int}
        namespace["total_count"] = total_count
        namespace["resolve_connection"] = resolve_connection

    # ``description=None`` keeps the opted variant's shipped description-less
    # SDL shape (the bare/opted description asymmetry is shipped surface - see
    # ``_connection_type_for``).
    generated = _generate_connection_class(target_type, _populate, description=None)
    return generated


def _guard_total_count_countable(nodes: Any, *, want_count: bool) -> None:
    """Raise ``GraphQLError`` when ``totalCount`` is selected over a non-queryset.

    The M1 carry-forward (Decision 7): ``totalCount`` renders ``Int!``, and a
    non-queryset iterable cannot be ``.count()``-ed. Rather than skip the count
    and let the ``Int!`` field return ``None`` (which surfaces as the engine's
    opaque ``Cannot return null for non-nullable field ...totalCount`` violation),
    raise a clear package error - symmetric with the sidecar-input rule in
    ``_post_process_consumer_*``. Single-sited so the sync and async count
    helpers share one rule.
    """
    if want_count and not isinstance(nodes, models.QuerySet):
        raise GraphQLError(
            "`totalCount` was selected on a connection whose resolver returned a "
            "non-queryset iterable; `totalCount` requires a QuerySet source it "
            "can count. Return a QuerySet (or a Manager) from the connection "
            "resolver, or do not select `totalCount`.",
        )


def _attach_count_sync(conn: Any, nodes: Any, *, want_count: bool) -> Any:
    """Attach the post-filter pre-slice count to a resolved connection (sync)."""
    _guard_total_count_countable(nodes, want_count=want_count)
    if want_count:
        setattr(conn, _TOTAL_COUNT_ATTR, nodes.count())
    return conn


async def _attach_count_async(conn_awaitable: Any, nodes: Any, *, want_count: bool) -> Any:
    """Attach the post-filter pre-slice count to a resolved connection (async)."""
    # Await-before-raise (mirrors the close-before-raise discipline in
    # ``utils/querysets.py::apply_type_visibility_sync``, Decision 10): resolve the
    # queued connection coroutine BEFORE the guard can raise, so a guard-raise
    # never leaves ``conn_awaitable`` unawaited (which would emit a
    # ``RuntimeWarning`` - a hard failure under ``-W error``). The guard's
    # decision depends only on ``nodes`` / ``want_count``, never on ``conn``,
    # so awaiting first is side-effect-safe.
    conn = await conn_awaitable
    _guard_total_count_countable(nodes, want_count=want_count)
    if want_count:
        setattr(conn, _TOTAL_COUNT_ATTR, await nodes.acount())
    return conn


def _connection_type_for(target_type: type) -> type:
    """Return (and cache) the connection class for a node ``DjangoType``.

    Always returns a generated concrete ``<TypeName>Connection`` subclass of
    ``DjangoConnection[target_type]``. ``target_type``'s ``definition.connection``
    slot (the validated ``Meta.connection`` value) only controls the shape:
    opting into ``total_count`` adds the ``totalCount`` members; otherwise the
    subclass adds nothing over the base. Cached on ``target_type`` identity -
    one connection shape per node type, no per-field override (Decision 5), so
    the generated name is unique and regeneration is avoided.
    """
    cached = _connection_type_cache.get(target_type)
    if cached is not None:
        return cached

    definition = target_type.__django_strawberry_definition__
    connection_options = definition.connection
    if connection_options and connection_options.get("total_count"):
        connection_type: type = _build_total_count_connection(target_type)
    else:
        # WHY concrete and not the ``DjangoConnection[target_type]`` alias:
        # handing the schema a generic ALIAS loses the package's
        # ``resolve_connection`` override - Strawberry's schema-build generic
        # specialization copies the alias into a plain specialized class whose
        # ``resolve_connection`` is ``ListConnection``'s, so the ``first`` +
        # ``last`` guard never ran through-schema (the spec-032 Slice-4
        # discovered bug). A concrete class is used as-is by the schema build,
        # so the override survives. The description is read from the parent's
        # strawberry definition (never copied as a package literal), preserving
        # the previous bare-alias SDL byte-for-byte.
        connection_type = _generate_connection_class(
            target_type,
            description=DjangoConnection.__strawberry_definition__.description,
        )
    _connection_type_cache[target_type] = connection_type
    return connection_type


# =============================================================================
# DjangoConnectionField - factory, synthesized-signature resolver, pipeline
# =============================================================================


def _guard_sidecar_input_against_non_queryset(source: Any, *, has_sidecar_input: bool) -> None:
    """Raise ``GraphQLError`` when ``filter:`` / ``orderBy:`` is supplied over a non-queryset.

    The consumer-``resolver=`` contract (Decision 7): a non-queryset iterable
    (list / generator) may be paginated only when NO ``filter:`` / ``orderBy:``
    input is supplied. The advertised Meta-driven filter/order behavior is a
    queryset operation and cannot apply to a plain iterable, so supplying
    sidecar input against one is a clear package error rather than a silently
    ignored argument. Symmetric with the ``totalCount`` rule in
    ``_guard_total_count_countable``.
    """
    if has_sidecar_input and not isinstance(source, models.QuerySet):
        raise GraphQLError(
            "`filter:` / `orderBy:` was supplied to a connection whose resolver "
            "returned a non-queryset iterable; these arguments narrow a QuerySet "
            "and cannot apply to a plain iterable. Return a QuerySet (or a "
            "Manager) from the connection resolver, or omit `filter:` / `orderBy:`.",
        )


def _guard_source_not_pre_sliced(source: models.QuerySet) -> None:
    """Raise ``GraphQLError`` when the connection resolver returns an already-sliced QuerySet.

    A ``DjangoConnectionField`` owns pagination: ``_finalize_queryset`` appends a
    deterministic total order and then Strawberry's ``ListConnection`` slices the
    QuerySet to the requested cursor window. Both are illegal on a QuerySet the
    resolver already sliced (``Category.objects.all()[:5]``) - Django forbids
    reordering or re-slicing a sliced query (``Cannot reorder a query once a slice
    has been taken``). Left unguarded the pipeline's ``order_by`` leaked that as a
    raw ``TypeError`` at the GraphQL boundary; this converts it to a clear,
    actionable ``GraphQLError`` naming the cause and the fix. Fires regardless of
    ``filter:`` / ``orderBy:`` input (the connection reorders and slices on every
    request), symmetric with ``_guard_sidecar_input_against_non_queryset``: a
    structural misuse of the connection ``resolver=`` contract surfaces as a
    package error, never a leaked Django internal.
    """
    if source.query.is_sliced:
        raise GraphQLError(
            "A connection resolver returned an already-sliced QuerySet (e.g. "
            "`qs[:10]`). A connection field manages its own ordering and cursor "
            "pagination, and Django forbids reordering or re-slicing a sliced "
            "query, so an already-sliced source cannot be paginated. Return an "
            "unsliced QuerySet (or a Manager) and let the connection's `first` / "
            "`last` / `before` / `after` arguments paginate it.",
        )


def _finalize_queryset(target_type: type, qs: models.QuerySet, info: Info) -> models.QuerySet:
    """Apply the color-agnostic pipeline tail: deterministic total order, then optimizer plan.

    Steps 5-6 of the Decision 7 pipeline. Single-sited so the sync and async
    resolver bodies share one implementation of the steps that do no I/O (the
    default ``order_by`` and the optimizer plan are pure queryset-method calls
    on a lazy queryset):

    5. Deterministic TOTAL ordering - the connection's positional offset cursors
       (Strawberry's ``ListConnection``) are only stable across separate
       requests when the ``ORDER BY`` is a unique total order. So append the pk
       as a terminal tiebreaker UNLESS the effective ordering already ends in a
       unique column. The decision lives in
       ``optimizer/plans.py::deterministic_order`` (hoisted there per spec-033
       Decision 11 so the plan-time window order and this resolve-time order can
       never disagree - the cursor-parity invariant). This covers all three
       cases - fully unordered, a supplied ``orderBy``, and a model
       ``Meta.ordering`` - not just the unordered one.

       The effective ordering must NOT be read from ``qs.query.order_by`` alone:
       that tuple is EMPTY when the order comes from model ``Meta.ordering``
       (Django applies ``_meta.ordering`` implicitly) even though ``qs.ordered``
       is True, so reading it in isolation would drop ``Meta.ordering`` and
       rewrite ``ORDER BY name`` into ``ORDER BY pk``. Fall back to
       ``_meta.ordering`` when ``qs.query.order_by`` is empty.
    6. Optimizer plan - ``apply_connection_optimization`` applies
       ``select_related`` / ``prefetch_related`` / ``only()`` using the node
       type / model explicitly (the connection field's own cooperation point,
       Decision 11), because the schema middleware never sees the pre-slice
       queryset behind ``ConnectionExtension``.
    """
    target_model = model_for(target_type)
    effective = tuple(qs.query.order_by) or tuple(target_model._meta.ordering)
    # Deterministic total order shared with the plan-time window (the
    # cursor-parity invariant, spec-033 Decision 11): the helper appends the pk
    # as a terminal tiebreaker unless the effective ordering already ends in a
    # unique column.
    ordered = deterministic_order(effective, target_model)
    if ordered != effective:
        qs = qs.order_by(*ordered)
    return apply_connection_optimization(target_type, qs, info)


def _prepare_pipeline_source(
    source: Any,
    *,
    filter_input: Any,
    order_by_input: Any,
) -> tuple[Any, bool]:
    """Normalize the pipeline source and apply the non-queryset sidecar guard.

    The color-agnostic head shared by ``_pipeline_sync`` / ``_pipeline_async``:
    a ``Manager`` is coerced to its ``QuerySet``; a non-queryset iterable passes
    the ``filter:`` / ``orderBy:`` guard here and is returned with
    ``is_queryset=False`` so the caller short-circuits and returns it unchanged.
    A QuerySet passes the pre-sliced guard (the connection reorders and slices it,
    both illegal on an already-sliced query) before flowing into the colored
    steps. Returns ``(source, is_queryset)`` rather than returning early itself so
    the sync and async pipelines keep their colored steps (the
    ``apply_type_visibility_*`` calls) explicit, never hidden behind a maybe-await
    abstraction. The ``Manager`` -> ``QuerySet`` coercion + is-queryset decision
    is the shared ``utils/querysets.py::normalize_query_source`` contract; only
    the connection's GraphQL-specific guards stay local here.
    """
    source, is_queryset = normalize_query_source(source)
    if not is_queryset:
        _guard_sidecar_input_against_non_queryset(
            source,
            has_sidecar_input=has_connection_sidecar_input(
                filter_input=filter_input,
                order_by_input=order_by_input,
            ),
        )
        return source, False
    _guard_source_not_pre_sliced(source)
    return source, True


def _pipeline_sync(
    target_type: type,
    source: Any,
    info: Info,
    *,
    filter_input: Any,
    order_by_input: Any,
) -> Any:
    """Run the composition pipeline on the sync path (Decision 7 / Decision 10).

    ``source`` is the base value (the consumer ``resolver=`` return or the
    default ``initial_queryset``). A ``Manager`` is coerced to a ``QuerySet``;
    a ``QuerySet`` receives steps 2-6 (visibility -> filter -> orderBy ->
    default-order -> optimizer); a non-queryset iterable is passed through
    unchanged after the sidecar-input guard rejects ``filter:`` / ``orderBy:``.
    """
    definition = target_type.__django_strawberry_definition__
    source, is_queryset = _prepare_pipeline_source(
        source,
        filter_input=filter_input,
        order_by_input=order_by_input,
    )
    if not is_queryset:
        return source
    qs = apply_type_visibility_sync(target_type, source, info)
    if filter_input is not None and definition.filterset_class is not None:
        qs = definition.filterset_class.apply_sync(filter_input, qs, info)
    if order_by_input is not None and definition.orderset_class is not None:
        qs = definition.orderset_class.apply_sync(order_by_input, qs, info)
    return _finalize_queryset(target_type, qs, info)


async def _pipeline_async(
    target_type: type,
    source: Any,
    info: Info,
    *,
    filter_input: Any,
    order_by_input: Any,
) -> Any:
    """Async sibling of ``_pipeline_sync`` - awaits the colored visibility / filter / order steps."""
    definition = target_type.__django_strawberry_definition__
    source, is_queryset = _prepare_pipeline_source(
        source,
        filter_input=filter_input,
        order_by_input=order_by_input,
    )
    if not is_queryset:
        return source
    qs = await apply_type_visibility_async(target_type, source, info)
    if filter_input is not None and definition.filterset_class is not None:
        qs = await definition.filterset_class.apply_async(filter_input, qs, info)
    if order_by_input is not None and definition.orderset_class is not None:
        qs = await definition.orderset_class.apply_async(order_by_input, qs, info)
    return _finalize_queryset(target_type, qs, info)


def _synthesized_signature(target_type: type) -> tuple[inspect.Signature, dict[str, Any]]:
    """Build the resolver ``__signature__`` + ``__annotations__`` carrying the sidecar args.

    Decision 6: the resolver's signature is the SDL contract. The return
    annotation is ``Iterable[target_type]`` (which ``ConnectionExtension.apply``
    requires); ``info`` is included so the resolver receives it; ``filter`` /
    ``order_by`` are added only for the sidecars the type declares, with the
    SAME ``filter_input_type(FS)`` / ``list[order_input_type(OS)]`` lazy
    ``Annotated`` shapes a hand-written filter/order resolver uses. Calling
    those helpers ALSO registers the FilterSet / OrderSet against the
    ``_helper_referenced_filtersets`` / ``_helper_referenced_ordersets`` orphan
    ledgers, so ``finalize_django_types`` orphan validation stays honest - no
    separate ``.add(...)`` is needed or wanted. The ``search:`` argument is NOT
    generated (search is ``0.1.2``).
    """
    # Imported at call time (schema build), not module scope: a module-level
    # import would make bare ``import django_strawberry_framework`` (which pulls
    # in ``connection`` via ``__init__``) eagerly import the ``filters`` /
    # ``orders`` subpackages, breaking the lazy-subpackage contract pinned by
    # ``tests/filters/test_finalizer.py`` and ``tests/orders/test_inputs.py``.
    # These helpers are only needed when building a field's synthesized
    # signature, so a function-local import keeps the top-level package import
    # lazy while preserving the generated ``filter:`` / ``orderBy:`` arguments.
    from .filters import filter_input_type
    from .orders import order_input_type

    definition = target_type.__django_strawberry_definition__
    # ``root`` and ``info`` are Strawberry reserved parameter names: the engine
    # binds the source value to ``root`` and the resolver ``Info`` to ``info``
    # WITHOUT exposing either as a GraphQL argument. Declaring them in the
    # synthesized signature means Strawberry passes both at call time (so the
    # consumer-``resolver=`` path gets ``root`` / ``info``) while only the
    # sidecar params below become real arguments.
    params: list[inspect.Parameter] = [
        inspect.Parameter("root", inspect.Parameter.POSITIONAL_OR_KEYWORD, default=None),
        inspect.Parameter("info", inspect.Parameter.KEYWORD_ONLY, annotation=Info),
    ]
    annotations: dict[str, Any] = {"info": Info}
    if definition.filterset_class is not None:
        filter_ann = filter_input_type(definition.filterset_class) | None
        params.append(
            inspect.Parameter(
                CONNECTION_FILTER_KWARG,
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
                annotation=filter_ann,
            ),
        )
        annotations[CONNECTION_FILTER_KWARG] = filter_ann
    if definition.orderset_class is not None:
        order_ann = list[order_input_type(definition.orderset_class)] | None
        params.append(
            inspect.Parameter(
                CONNECTION_ORDER_KWARG,
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
                annotation=order_ann,
            ),
        )
        annotations[CONNECTION_ORDER_KWARG] = order_ann
    return_annotation = Iterable[target_type]
    annotations["return"] = return_annotation
    return inspect.Signature(params, return_annotation=return_annotation), annotations


def _build_connection_resolver(target_type: type, resolver: Callable | None) -> Callable:
    """Build the field resolver: the pipeline body plus the synthesized signature.

    The body pops ``filter`` / ``order_by`` (forwarded by ``ConnectionExtension``
    as ``**kwargs``) and runs the composition pipeline. Sync-vs-async dispatch is
    committed per-construction (Decision 10), because Strawberry freezes a
    field's resolver sync/async handling at schema-build time AND, unlike a plain
    field, ``ConnectionExtension`` only awaits an awaitable inner-resolver return
    when the field is async (``ConnectionExtension.resolve`` - the sync path -
    passes the resolver return straight to ``resolve_connection`` without
    awaiting; only ``resolve_async`` awaits). So a per-call coroutine return from
    a sync resolver (the ``DjangoListField`` shape) would NOT be awaited here:

    - **Default branch** (``resolver is None``) and the **sync consumer-resolver**
      branch are sync resolvers running ``_pipeline_sync``, which returns a LAZY
      queryset. A lazy queryset works under BOTH ``execute_sync`` and
      ``await execute`` - ``resolve_connection`` / ``ListConnection`` materialize
      it with ``.count()`` (sync) or ``.acount()`` (async) per the runtime
      context, so async counting still happens for the default field. A sync
      pipeline meeting an async ``get_queryset`` raises ``SyncMisuseError`` (the
      Relay-foundation contract); to drive an async ``get_queryset`` hook through
      a connection, supply an ``async def`` ``resolver=`` (below).
    - **Async consumer-resolver** branch (``is_async_callable(resolver)``) is an
      ``async def`` resolver running ``_pipeline_async`` - being ``async def``
      makes the field async, so ``ConnectionExtension.resolve_async`` awaits its
      return and the async ``get_queryset`` / ``apply_async`` hooks run on the
      async path.
    """
    if resolver is None:

        def _resolve(root: Any, info: Info, **kwargs: Any) -> Any:  # noqa: ARG001
            filter_input, order_by_input = connection_sidecar_inputs_from_kwargs(kwargs)
            return _pipeline_sync(
                target_type,
                initial_queryset(target_type),
                info,
                filter_input=filter_input,
                order_by_input=order_by_input,
            )

    elif is_async_callable(resolver):

        async def _resolve(root: Any, info: Info, **kwargs: Any) -> Any:
            source = await resolver(root, info)
            filter_input, order_by_input = connection_sidecar_inputs_from_kwargs(kwargs)
            return await _pipeline_async(
                target_type,
                source,
                info,
                filter_input=filter_input,
                order_by_input=order_by_input,
            )

    else:

        def _resolve(root: Any, info: Info, **kwargs: Any) -> Any:
            filter_input, order_by_input = connection_sidecar_inputs_from_kwargs(kwargs)
            return _pipeline_sync(
                target_type,
                resolver(root, info),
                info,
                filter_input=filter_input,
                order_by_input=order_by_input,
            )

    signature, annotations = _synthesized_signature(target_type)
    _resolve.__signature__ = signature
    _resolve.__annotations__ = annotations
    return _resolve


def _window_rows_are_annotated(rows: list) -> bool:
    """Return whether every row carries the windowed-prefetch row number.

    Upstream's own integrity probe (``resolve_optimized_connection_by_prefetch``
    falls back on a missing annotation): a ``to_attr`` list whose rows lack
    ``_dst_row_number`` is a consumer's own prefetch write, not the walker's
    window, and must NOT be consumed as one. ``_dst_total_count`` is NOT
    probed: the walker annotates it conditionally (connection window rigor,
    workstream B - only when ``totalCount`` / ``hasNextPage`` / the window
    shape needs it), so a count-less page is still the walker's window. The
    collision probe stays sound on the row number alone because the ``_dst_``
    namespace is package-reserved (spec-033 Decision 4). An empty list has no
    rows to probe and is still a valid window candidate (a genuinely-empty or
    ambiguous-empty page); the empty case is classified in
    ``resolve_connection`` where the slice metadata is known.
    """
    return all(hasattr(row, WINDOW_ROW_NUMBER) for row in rows)


def _build_relation_connection_resolver(
    target_type: type,
    accessor_name: str,
    relation_field_name: str,
    declaring_type: type,
) -> Callable:
    """Build the resolver for a Phase-2.5 synthesized relation connection (spec-032 Decision 6).

    Identical pipeline tail to ``_build_connection_resolver``'s default branch,
    but the source queryset seeds from the PARENT'S relation manager
    (``getattr(root, accessor_name).all()``) - keeping Django's prefetch caches
    reachable as the cooperation seam ``WIP-ALPHA-033-0.0.9``'s
    window-pagination planning uses - instead of
    ``model._default_manager.all()``. ``accessor_name`` is the same
    ``field.name`` the shipped many-side list resolver reads
    (``types/resolvers.py::many_resolver``), so the list field and its
    connection sibling can never disagree about which manager they traverse.

    The fast-path handoff (spec-033 Decision 5): when the walker's windowed
    prefetch fired it lands the page under the package-reserved ``to_attr``
    ``_dst_<field>_connection`` (keyed on ``relation_field_name``, NOT the
    accessor - the two DIVERGE for a reverse relation without ``related_name``,
    ``book`` vs ``book_set``, so probing the accessor would silently never fire
    the fast path). The resolver probes that ``to_attr`` and, when the rows
    carry the window annotations AND the resolver's own ``filter`` / ``order_by``
    kwargs are absent, returns a ``_WindowedConnectionRows`` marker handing the
    rows to the generated connection class (which builds the Relay object - the
    resolver never constructs a connection, since Strawberry feeds the resolver
    return back through ``resolve_connection`` as the node iterable). A sidecar
    kwarg present means the window is ignored and the pipeline runs, so a future
    planner/argument desync can never serve unfiltered wrong data. The marker
    also carries a fallback factory re-running this pipeline, which
    ``resolve_connection`` invokes for an ambiguous-empty window (``first: 0`` /
    overshot ``after:``) it cannot classify (the resolver never sees the
    pagination arguments - ``ConnectionExtension`` consumes them).

    Sync resolver returning a LAZY queryset by design (the
    committed-at-construction contract on ``_build_connection_resolver`` holds
    verbatim: a lazy queryset works under both ``execute_sync`` and
    ``await execute``). Strictness (spec-033 Decision 8): before running the
    per-parent fallback pipeline, the resolver consults the union-published
    optimizer sentinels via the parameterized
    ``types/resolvers.py::_check_n1`` (``kind="connection_to_attr"``) - an
    unplanned, unserved nested-connection access fires ``OptimizerError`` under
    ``"raise"`` / a logged warning under ``"warn"`` through the SAME machinery
    list relations use, never a second checker. ``declaring_type`` is the
    ``DjangoType`` whose ``Meta`` declared this relation; it is the
    ``parent_type`` the walker keyed the planned connection under
    (``resolver_key(type_cls, relation_field_name, runtime_path)``), so passing
    it - paired with ``relation_field_name`` (NOT the generated connection name)
    and the resolve-time runtime path - is what makes the resolver-side key
    MATCH the walker's emission, the load-bearing parity for "planned -> silent".

    Async-``get_queryset`` posture (0.0.9): this is sync-pipeline-only and has
    no ``resolver=`` seam (the documented escape a *root* connection uses for
    an async hook), so a Relay target whose ``get_queryset`` is ``async def``
    raises ``SyncMisuseError`` on every query of its synthesized
    ``<field>Connection``; ``relation_shapes = {"<field>": "list"}`` is the
    recourse until an async connection pipeline rides the ``033`` work. The
    fail-loud ``SyncMisuseError`` is inherited from the pipeline, not new here.
    """
    to_attr = _relation_connection_to_attr(relation_field_name)

    def _resolve(root: Any, info: Info, **kwargs: Any) -> Any:
        source = getattr(root, accessor_name).all()
        window_rows = getattr(root, to_attr, None)
        filter_input, order_by_input = connection_sidecar_inputs_from_kwargs(kwargs)
        no_sidecar = not has_connection_sidecar_input(
            filter_input=filter_input,
            order_by_input=order_by_input,
        )
        if (
            isinstance(window_rows, list)
            and no_sidecar
            and _window_rows_are_annotated(window_rows)
        ):
            # Hand off the windowed page. The marker carries a fallback factory
            # (NOT a prebuilt connection - that would be fed back through
            # ``resolve_connection`` as the node iterable) so ``resolve_connection``
            # can recover this per-parent pipeline for an ambiguous-empty window.
            return _WindowedConnectionRows(
                rows=window_rows,
                fallback=_build_windowed_fallback(target_type, source, info),
            )
        # Strictness (spec-033 Decision 8): consult the union-published
        # sentinels via the parameterized ``_check_n1`` BEFORE the per-parent
        # pipeline. The reason names WHY the fallback fired so a flagged
        # connection reads as actionable: a sidecar (``filter:`` / ``orderBy:``)
        # selection is the explicitly-unwindowed shape (Decision 6), so it
        # carries the spec's filter/orderBy wording; any other fallback gets the
        # generic per-parent reason.
        reason = (
            "not window-planned: selection carries filter/orderBy; resolving per-parent"
            if not no_sidecar
            else "not window-planned; resolving per-parent"
        )
        _check_n1(
            info,
            root,
            relation_field_name,
            declaring_type,
            kind="connection_to_attr",
            to_attr=to_attr,
            reason=reason,
        )
        return _pipeline_sync(
            target_type,
            source,
            info,
            filter_input=filter_input,
            order_by_input=order_by_input,
        )

    signature, annotations = _synthesized_signature(target_type)
    _resolve.__signature__ = signature
    _resolve.__annotations__ = annotations
    return _resolve


def DjangoConnectionField(  # noqa: N802  # PascalCase for graphene-django parity - consumer usage is `DjangoConnectionField(GenreType)`
    target_type: type,
    *,
    resolver: Callable | None = None,
    description: str | None = None,
    deprecation_reason: str | None = None,
    directives: Sequence[object] = (),
) -> Any:
    """Factory for a Relay connection field over a Relay-Node-shaped ``DjangoType``.

    Meta-only derivation (Decision 5): the ``filter:`` / ``orderBy:`` arguments
    come from the type's ``Meta.filterset_class`` / ``Meta.orderset_class``, the
    ``totalCount`` opt-in from ``Meta.connection`` - there are no ``filters=`` /
    ``order=`` / ``total_count=`` keyword arguments. Runs the four
    ``DjangoListField``-style guards plus a Relay-Node guard, then returns
    ``relay.connection(_connection_type_for(target_type), resolver=<synthesized>,
    ...)`` (Decision 6 / Decision 7).

    Consumer ``resolver=`` contract: the resolver is invoked as
    ``resolver(root, info)`` and returns only the BASE queryset / manager /
    iterable. It never receives the ``filter:`` / ``orderBy:`` arguments - the
    synthesized resolver consumes those and the pipeline applies them to the
    resolver's return (the same shape as ``DjangoListField``). A resolver that
    declares its own ``filter`` / ``order_by`` parameters will not be handed
    them; use ``Meta.filterset_class`` / ``Meta.orderset_class`` to shape the
    sidecar arguments.
    """
    # The four shared ``DjangoType``-target guards plus the connection-specific
    # Relay-Node-shaped guard, single-sited in
    # ``list_field.py::_validate_relay_djangotype_target`` (shared with the node
    # fields per the 0.0.9 DRY pass). Its ``_is_relay_shaped`` check accepts
    # EITHER spelling at construction time: ``relay.Node`` in the declared
    # ``Meta.interfaces`` tuple (populated at class creation, before Phase 2.5
    # ``apply_interfaces`` injects it into ``__bases__`` -- a plain MRO check
    # would wrongly reject it here) OR direct ``relay.Node`` inheritance.
    _validate_relay_djangotype_target(
        target_type,
        resolver,
        field="DjangoConnectionField",
        relay_error_message=(
            "a connection field requires a Relay-Node-shaped DjangoType; add "
            "`relay.Node` to `Meta.interfaces` (or inherit `relay.Node` directly)"
        ),
    )
    return relay.connection(
        _connection_type_for(target_type),
        resolver=_build_connection_resolver(target_type, resolver),
        description=description,
        deprecation_reason=deprecation_reason,
        directives=directives,
    )
