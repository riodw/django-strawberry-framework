"""``DjangoConnection[T]`` + ``DjangoConnectionField`` - the Relay cursor-pagination surface.

Spec: ``docs/spec-030-connection_field-0_0_9.md``.
Target release: ``0.0.9``.

Slice 1's surface (Decision 3 / Decision 4):

- ``DjangoConnection[NodeType]`` - a generic ``strawberry.relay.ListConnection``
  subclass that owns the package's ``first`` + ``last`` mutual-exclusivity
  guard (which Strawberry's ``SliceMetadata.from_arguments`` does NOT provide),
  consumes optimized nested windows, and dispatches keyset-mode connections to
  the package slicer. It carries no ``total_count`` field; ordinary non-window
  offset sources still delegate to Strawberry's ``ListConnection``.
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
from collections.abc import AsyncIterable, AsyncIterator, Callable, Iterable, Sequence
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import Any, Generic, TypeVar

import strawberry
from django.db import models
from graphql import GraphQLError
from strawberry import relay
from strawberry.relay.types import NodeIterableType
from strawberry.relay.utils import should_resolve_list_connection_edges
from strawberry.types import Info, get_object_definition
from strawberry.utils.await_maybe import AwaitableOrValue
from strawberry.utils.inspect import in_async_context

from .keyset import (
    CursorColumn,
    KeysetSeek,
    _is_supported_cursor_field,
    cursor_columns_for,
    decode_keyset_cursor,
    encode_keyset_cursor,
    order_fingerprint,
)
from .list_field import _validate_relay_djangotype_target
from .optimizer.extension import apply_connection_optimization
from .optimizer.nested_planner import (
    _extend_only_projection,
    _relation_connection_to_attr,
    _relation_connection_to_attr_for_key,
)
from .optimizer.plans import (
    WINDOW_KEYSET_SEEK_COUNT,
    WINDOW_ROW_NUMBER,
    WINDOW_TOTAL_COUNT,
    deterministic_order,
    ends_in_unique_column,
    order_entry_name_and_direction,
)
from .optimizer.selections import (
    connection_has_next_page_selected,
    connection_total_count_selected,
    prime_selected_fields,
)
from .registry import register_subsystem_clear
from .types.resolvers import _check_n1
from .utils.connections import (
    CONNECTION_FILTER_KWARG,
    CONNECTION_ORDER_KWARG,
    UnwindowableConnection,
    connection_sidecar_inputs_from_kwargs,
    derive_connection_window_bounds,
    derive_keyset_window_bounds,
    has_connection_sidecar_input,
    resolve_relay_max_results,
    split_window_rows,
    window_range_plan,
)
from .utils.querysets import (
    apply_type_visibility_async,
    apply_type_visibility_sync,
    initial_queryset,
    model_for,
    normalize_query_source,
    reject_awaitable_sync_source,
    reject_residual_async_source,
)
from .utils.relations import relation_kind
from .utils.typing import is_async_callable, unwrap_container_type

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


@dataclass(frozen=True)
class _KeysetConnectionState:
    """The keyset-mode context a generated connection class resolves once.

    ``columns`` / ``fingerprint`` are the DECLARED ``Meta.cursor_field``
    contract - the vocabulary every nested window and default-ordered root
    page mints and decodes under. A root ``orderBy:`` page derives its own
    per-order columns/fingerprint instead (``_keyset_order_state``); the
    declared state still marks the connection as keyset-mode.
    """

    definition: Any
    cursor_field: tuple[str, ...]
    columns: tuple[CursorColumn, ...]
    fingerprint: str


def _keyset_connection_context(cls: type) -> _KeysetConnectionState | None:
    """Resolve (and cache on the class) a connection's keyset-mode state.

    The generated ``<TypeName>Connection`` carries its node type on
    ``_dst_node_type`` (stashed by ``_generate_connection_class``); a
    declared ``Meta.cursor_field`` on that type's definition makes every
    connection over it KEYSET-MODE - value cursors minted/decoded through
    the canonical codec, offset cursors rejected. ``None`` (the cached
    ``False`` sentinel internally) keeps the shipped offset behavior.
    """
    cached = cls.__dict__.get("_dst_keyset_state")
    if cached is not None:
        return cached or None
    target_type = getattr(cls, "_dst_node_type", None)
    definition = getattr(target_type, "__django_strawberry_definition__", None)
    cursor_field = getattr(definition, "cursor_field", None)
    state: Any = False
    if cursor_field is not None:
        state = _KeysetConnectionState(
            definition=definition,
            cursor_field=cursor_field,
            columns=cursor_columns_for(definition.model, cursor_field),
            fingerprint=order_fingerprint(cursor_field),
        )
    cls._dst_keyset_state = state
    return state or None


def _set_total_count(conn: Any, *, want_count: bool, value: Any) -> Any:
    """Attach the captured ``totalCount`` to ``conn`` when it was requested.

    The single writer of ``_TOTAL_COUNT_ATTR`` (the selection-gating contract:
    an unrequested count stays the ``None`` default the ``total_count``
    resolver returns verbatim). ``value`` may be a zero-arg callable evaluated
    only when the count IS wanted, so callers can pass a lazy ``.count()``
    without spelling the guard themselves. Returns ``conn`` for tail-position
    use.
    """
    if want_count:
        setattr(conn, _TOTAL_COUNT_ATTR, value() if callable(value) else value)
    return conn


def _empty_page_connection(
    cls: type,
    *,
    offset: int,
    has_next_page: bool,
    want_count: bool,
    total: int,
    has_previous_page: bool | None = None,
) -> Any:
    """Build the edge-less connection the window fast path serves.

    One home for the pipeline-parity-bearing empty-page shape (the zero-children
    page and the marker-only empty page differ ONLY in ``has_next_page`` and the
    served ``total``): ``has_previous_page = offset > 0`` replicates
    ``ListConnection``'s ``start > 0`` arithmetic, computed before the data is
    consulted - a childless parent with ``after:`` still reports a previous
    page, exactly like the per-parent pipeline. A keyset window has no offset
    domain, so its caller passes ``has_previous_page`` explicitly ("a cursor
    was supplied" - the same rule ``start > 0`` encodes for offset cursors).
    """
    conn = cls(
        edges=[],
        page_info=relay.PageInfo(
            start_cursor=None,
            end_cursor=None,
            has_previous_page=offset > 0 if has_previous_page is None else has_previous_page,
            has_next_page=has_next_page,
        ),
    )
    return _set_total_count(conn, want_count=want_count, value=total)


@dataclass
class _WindowedConnectionRows:
    """Internal marker handing windowed prefetch rows to ``resolve_connection``.

    The synthesized relation-connection resolver (Decision 5) returns this in
    place of the per-parent node iterable when the walker's windowed prefetch
    fired: ``rows`` is the ``_dst_<field>_connection`` ``to_attr`` list of
    annotated model instances (each carrying ``_dst_row_number`` /
    conditionally ``_dst_total_count``), and ``fallback`` re-runs the shipped
    per-parent pipeline only when the wrapper cannot be served safely. Planned
    ``first: 0``, overshot offset ``after:``, and corresponding forward keyset
    empty pages retain marker rows and are served directly. The callable remains
    the defensive recovery seam for shapes such as ``last: 0``, a backward
    keyset wrapper, or missing required count/seek annotations.

    The resolver lacks the pagination arguments needed to classify the rows
    itself (Strawberry's ``ConnectionExtension.resolve`` consumes ``first`` /
    ``last`` / ``before`` / ``after`` and forwards them only to
    ``resolve_connection``), so all window classification happens there.

    NOT a connection instance and NOT exported (no public symbol - spec
    "adds no public symbol"); the ``resolve_connection`` paths
    ``isinstance``-detect it after the ``first`` + ``last`` guard.
    """

    rows: list[Any]
    fallback: Callable[[], Any] = dataclass_field(repr=False)


def _build_windowed_fallback(target_type: type, source: Any, info: Info) -> Callable[[], Any]:
    """Return a zero-arg callable re-running the per-parent pipeline.

    Carried on ``_WindowedConnectionRows`` so ``resolve_connection`` can recover
    the shipped per-parent queryset when a handed-off wrapper cannot be served
    safely, without the walker's slice helper or the live relation manager
    (which the resolver, not ``resolve_connection``, holds). Normal marker-only
    empty pages do not call it. ``source`` is the same
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
    ``Edge`` subclass via the bounded ``unwrap_container_type`` (DRY review B3 -
    the container-scoped, Power-of-Ten-capped peel), so the fast path builds
    edges through Strawberry's own edge type (cursor PREFIX + base64 stay owned
    there - the fast path passes only the integer offset).
    """
    type_def = get_object_definition(cls, strict=True)
    field_def = type_def.get_field("edges")
    return unwrap_container_type(field_def.resolve_type(type_definition=type_def))


def _resolve_from_window(
    cls: type,
    window: _WindowedConnectionRows,
    *,
    info: Info,
    offset: int,
    limit: int | None,
    reverse: bool = False,
    want_count: bool,
    keyset_state: _KeysetConnectionState | None = None,
    keyset_after: str | None = None,
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

    The common ``first: N`` page selecting ``pageInfo.hasNextPage`` but NOT
    ``totalCount`` is served count-free by the n+1 probe (``next_page_probe``):
    the walker overfetched ONE sentinel row past the page instead of a
    per-partition ``COUNT(1) OVER`` scan, so ``hasNextPage`` is the sentinel's
    presence (``probe_row_seen`` from ``split_window_rows``) rather than
    ``row_number < total``. This resolver reads the probe off the window's
    PHYSICAL shape - a ``plain_first_page`` window carrying no
    ``_dst_total_count`` annotation was overfetched (or needs no count) - NOT
    off this response key's ``info``: same-argument aliases merge into one
    shared window whose shape was fixed at plan time from the merged selection,
    so a per-alias re-derivation would drift (an edges-only alias would keep the
    sentinel). The output is byte-identical (same edges, cursors, ``hasNextPage``;
    ``totalCount`` not selected); only the SQL cost changes. ``split_window_rows``
    + the ``hasNextPage`` derivation here are the resolve-side surface a future
    keyset-cursor backend inherits: it makes ``_dst_row_number`` page-relative
    (so ``row_number < total`` no longer holds) and derives ``hasNextPage`` from
    this same overfetch, and ``hasPreviousPage`` from "a cursor was supplied".

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
    # Derive the count-free ``hasNextPage`` probe from the window's PHYSICAL
    # shape, NOT this response key's selection. Same-argument aliases merge into
    # ONE shared window (spec-033 Decision 6) whose overfetch/count shape is
    # fixed at PLAN time from the MERGED (union) selection - so re-deriving the
    # probe per alias from ``info`` would drift from that shared shape: an
    # edges-only alias would keep the overfetched sentinel row, and a
    # ``hasNextPage``-only alias beside a ``totalCount`` alias would read a stale
    # flag off an un-overfetched, counted window. The ``_dst_total_count``
    # annotation's presence on the rows IS the materialized plan decision. On the
    # ``plain_first_page`` shape (the only one a probe applies to) its ABSENCE
    # means the window was overfetched by the probe - or needs no count at all -
    # so ``hasNextPage`` is the sentinel's presence; a counted window keeps
    # ``row_number < total``. Reading ground truth, every alias sharing the
    # window resolves identically. ``window_range_plan`` is a pure construction;
    # the empty-``rows`` early return below never consults the probe flag, so
    # requiring ``rows`` here just avoids an inert rebuild.
    #
    # LOAD-BEARING plan-time invariant: this "count-absent -> overfetched"
    # inference is sound only because the walker keeps ``next_page_probe`` and
    # ``with_total_count`` mutually exclusive - a count-free ``plain_first_page``
    # window whose ``hasNextPage`` is OBSERVABLE is ALWAYS overfetched
    # (``wants_next_page_probe`` forces ``with_total_count=False``, walker.py's
    # ``_plan_connection_relation``). So count-absent here can only mean
    # overfetched OR no observer at all, never observable-but-not-overfetched. A
    # future optimization that produced a count-free non-overfetched first page
    # while ``hasNextPage`` is selected would under-report it - keep that
    # invariant if the count/overfetch decision ever changes.
    range_plan = window_range_plan(offset=offset, limit=limit, reverse=reverse)
    if (
        range_plan.plain_first_page
        and rows
        and getattr(rows[-1], WINDOW_TOTAL_COUNT, None) is None
    ):
        range_plan = window_range_plan(
            offset=offset,
            limit=limit,
            reverse=reverse,
            next_page_probe=True,
        )
    # A COUNTED keyset-seek window (a ``cursor_field`` page resolving
    # ``after:`` whose count is annotated) numbers rows PAGE-RELATIVELY (the
    # filtered running count; pre-seek rows carry 0) and keeps the abs-first
    # marker row - re-derive the plan with the keyset semantics so the split
    # below drops the rn-0 rows and classifies markers. The count-FREE keyset
    # seek needs nothing here: its seek lives in the base WHERE, its rows
    # number 1..N natively, and the probe inference above already covers it.
    keyset_seek_supplied = keyset_state is not None and keyset_after is not None
    if keyset_seek_supplied and rows and getattr(rows[-1], WINDOW_TOTAL_COUNT, None) is not None:
        range_plan = window_range_plan(
            offset=offset,
            limit=limit,
            reverse=reverse,
            keyset_counted=True,
        )
    if not rows:
        if reverse and limit == 0:
            # ``last: 0``: upstream ``ListConnection`` slices ``edges[-0:]``,
            # which is the WHOLE list - only the per-parent pipeline reproduces
            # that quirk, so the (always-empty) reversed window falls back.
            return None
        # With marker rows planned for the ambiguous shapes (workstream C) and
        # the n+1 sentinel for the count-free probe, an empty forward window now
        # PROVES the parent has no related rows for EVERY shape - a parent with
        # children would have kept its row 1 or its probe sentinel.
        # ``has_next_page`` False: no row survived the overfetch. A keyset seek
        # page has no offset domain, so its "a cursor was supplied" previous-page
        # rule is passed explicitly.
        return _empty_page_connection(
            cls,
            offset=offset,
            has_next_page=False,
            want_count=want_count,
            total=0,
            has_previous_page=True if keyset_seek_supplied else None,
        )

    # Sentinel exclusion via the shared ``split_window_rows``: the window may
    # carry marker rows (ambiguous ``after:`` / ``first: 0`` shapes, workstream
    # C) OR one probe sentinel (the count-free ``hasNextPage`` overfetch) - both
    # dropped from the page here, mutually exclusive by shape, so cursors are
    # untouched. ``probe_row_seen`` IS ``hasNextPage`` on the probe shape (a row
    # existed past the page); it is ``False`` for every other shape. The
    # splitter reads the range plan, so what the window PLANNED and what this
    # path CLASSIFIES cannot drift.
    page_rows, probe_row_seen = split_window_rows(
        rows,
        range_plan,
        row_number=WINDOW_ROW_NUMBER,
    )
    if not page_rows:
        # Marker-only window: children exist (the marker is one) but the page
        # is empty. Serve the true count and the pipeline's flag arithmetic:
        # ``has_next_page = total > offset`` (the overfetch probe - for
        # ``first: 0`` a row exists past the offset; for an overshot ``after:``
        # ``total <= offset`` by construction, so it is False). Unreachable on
        # the probe shape (its page always keeps row 1). A keyset seek page's
        # flags live in the value domain instead: ``has_next_page`` is "any
        # post-seek row exists" (the annotated seek count - zero here by
        # construction, since one such row would BE the page), and a supplied
        # cursor is the previous-page signal.
        total = getattr(rows[-1], WINDOW_TOTAL_COUNT, None)
        if total is None:
            return None  # workstream-B drift guard: never infer a count.
        if keyset_seek_supplied:
            has_next_page = bool(getattr(rows[-1], WINDOW_KEYSET_SEEK_COUNT, 0))
        else:
            has_next_page = total > offset
        return _empty_page_connection(
            cls,
            offset=offset,
            has_next_page=has_next_page,
            want_count=want_count,
            total=total,
            has_previous_page=True if keyset_seek_supplied else None,
        )
    # The count is annotated CONDITIONALLY (workstream B) - and NOT AT ALL for
    # the count-free ``hasNextPage`` probe. A count-less row with a count
    # observer requested that the probe does NOT serve means the plan-time
    # predicate and this resolve-time read have DRIFTED (they share the
    # selection walk in ``optimizer/selections.py``, so by construction this is
    # unreachable until they diverge) - fall back per-parent rather than serve a
    # wrong flag/count, checked BEFORE any edge is built so the fallback
    # discards no work. On the probe path the missing count is EXPECTED
    # (``hasNextPage`` comes from ``probe_row_seen``, ``totalCount`` is not
    # selected); without any observer the missing count is inert (the
    # ``has_next_page`` below is never serialized).
    last_row = page_rows[-1]
    total = getattr(last_row, WINDOW_TOTAL_COUNT, None)
    if total is None and (
        want_count or (_has_next_page_requested(info) and not range_plan.next_page_probe)
    ):
        return None
    if (
        keyset_seek_supplied
        and total is not None
        and getattr(last_row, WINDOW_KEYSET_SEEK_COUNT, None) is None
        and _has_next_page_requested(info)
    ):
        # The counted keyset drift guard, mirroring the count guard above: a
        # counted seek page whose ``hasNextPage`` is observable must carry the
        # post-seek count its flag reads from - fall back per-parent rather
        # than serve a page-relative-vs-pre-seek comparison.
        return None
    edge_class = _window_edge_class(cls)
    if keyset_state is not None:
        # Keyset cursors are the rows' ordering-column VALUES, minted through
        # the canonical codec (opaque, authenticated-encrypted) - never the
        # row number. Edges are constructed directly (``resolve_edge`` would re-encode the
        # cursor under the offset ``arrayconnection`` prefix).
        edges = [
            edge_class(
                node=cls.resolve_node(node, info=info, **kwargs),
                cursor=encode_keyset_cursor(
                    keyset_state.columns,
                    node,
                    fingerprint=keyset_state.fingerprint,
                ),
            )
            for node in page_rows
        ]
    else:
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
    # row is short of the total, OR - on the count-free probe path - when the
    # overfetch sentinel was present. These hold for the reversed ``last``-only
    # window too because its row numbers stay forward (``last: 2`` of 5 -> rows
    # 4, 5 -> hasPrevious True, hasNext False - matching the pipeline).
    #
    # Keyset seek pages fork BOTH flags into the value domain: the row numbers
    # are page-relative (1..N), so ``first_rn > 1`` can never fire - a supplied
    # cursor IS the previous-page signal - and ``rn < total`` compares
    # page-relative to pre-seek, so the counted shape reads the annotated
    # POST-SEEK count instead (missing annotation = plan drift: fall back
    # rather than serve a wrong flag).
    first_rn = getattr(page_rows[0], WINDOW_ROW_NUMBER)
    if range_plan.next_page_probe:
        has_next_page = probe_row_seen
    elif keyset_seek_supplied:
        # Count-free with no probe means nothing observes the flag (the
        # workstream-B drift guard above already sent an OBSERVED count-less
        # page per-parent), so a missing seek count here is the inert
        # placeholder case, never a served falsehood.
        seek_total = getattr(last_row, WINDOW_KEYSET_SEEK_COUNT, None)
        has_next_page = (
            False if seek_total is None else getattr(last_row, WINDOW_ROW_NUMBER) < seek_total
        )
    else:
        has_next_page = False if total is None else getattr(last_row, WINDOW_ROW_NUMBER) < total
    conn = cls(
        edges=edges,
        page_info=relay.PageInfo(
            start_cursor=edges[0].cursor,
            end_cursor=edges[-1].cursor,
            has_previous_page=keyset_seek_supplied or first_rn > 1,
            has_next_page=has_next_page,
        ),
    )
    return _set_total_count(conn, want_count=want_count, value=total)


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
    marker rows directly serve ``first: 0``, overshot offset ``after:``, and
    corresponding forward keyset empty pages. The carried per-parent fallback
    runs only for an unservable wrapper such as ``last: 0``, a defensive
    backward-keyset handoff, or required-annotation drift. Returns
    ``_NOT_A_WINDOW`` when ``nodes`` is not a wrapper, so the caller delegates
    to the shipped path.
    """
    if not isinstance(nodes, _WindowedConnectionRows):
        return _NOT_A_WINDOW
    # Derive the window through the SHARED contract the walker planned with
    # (``utils/connections.py::derive_connection_window_bounds`` - or its
    # keyset twin when the node type declares ``Meta.cursor_field``, since a
    # value cursor cannot pass through the offset ``SliceMetadata`` engine:
    # the bounds derivation FORKS AT THE CURSOR VOCABULARY), so the
    # resolve-time window matches the plan-time one by construction (the
    # cursor-parity invariant). Resolver arguments are already coerced by
    # Strawberry, so any malformed-pagination ``ValueError`` / ``TypeError``
    # propagates as the field's own error (the walker, by contrast, catches it to
    # leave the selection unplanned).
    keyset_state = _keyset_connection_context(cls)
    if keyset_state is not None:
        try:
            bounds = derive_keyset_window_bounds(
                info,
                before=before,
                after=after,
                first=first,
                last=last,
                max_results=max_results,
            )
        except UnwindowableConnection:
            # A backward keyset shape over a windowed wrapper: the walker
            # never plans one, so this is a defensive-only path - recover the
            # per-parent queryset and let the keyset slicer resolve it.
            built = None
        else:
            built = _resolve_from_window(
                cls,
                nodes,
                info=info,
                offset=bounds.offset,
                limit=bounds.limit,
                reverse=bounds.reverse,
                want_count=want_count,
                keyset_state=keyset_state,
                keyset_after=after,
                **kwargs,
            )
    else:
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

    The defensive recovery tail for a wrapper the fast path cannot serve:
    ``DjangoConnection.resolve_connection`` (which ``super()`` reaches) does the
    ``first`` + ``last`` guard and slicing; the ``totalCount`` variant additionally
    attaches the count. Reuses the inherited ``ListConnection`` slicing - no
    second offset-slice implementation.

    A KEYSET connection routes to the framework's keyset slicer instead:
    ``ListConnection`` can neither decode a value cursor nor mint one, so
    the codec-aware slicer is the fallback's slicing engine - the same
    engine root keyset connections use, which is what keeps the fallback's
    cursor bytes identical to every windowed path's (the cross-strategy
    parity invariant).
    """
    keyset_state = _keyset_connection_context(cls)
    if keyset_state is not None:
        return _resolve_keyset_connection(
            cls,
            nodes,
            info=info,
            want_count=want_count,
            state=keyset_state,
            **slice_kwargs,
        )
    conn = super(DjangoConnection, cls).resolve_connection(nodes, info=info, **slice_kwargs)
    if inspect.isawaitable(conn):
        return _attach_count_async(conn, nodes, want_count=want_count)
    return _attach_count_sync(conn, nodes, want_count=want_count)


def _keyset_order_ref(entry: Any) -> tuple[str, str, bool] | None:
    """Parse one effective-order entry into ``(canonical ref, name, descending)``.

    Accepts the string and plain-``OrderBy``/``F`` shapes
    ``order_entry_name_and_direction`` parses; rejects (``None``) entries a
    value cursor cannot anchor: unresolvable expressions (aggregates,
    transforms) and explicit ``nulls_first`` / ``nulls_last`` positioning
    (the nullable domain the v1 column contract excludes).
    """
    if not isinstance(entry, str) and (
        getattr(entry, "nulls_first", None) or getattr(entry, "nulls_last", None)
    ):
        return None
    parsed = order_entry_name_and_direction(entry)
    if parsed is None:
        return None
    name, descending = parsed
    return (f"-{name}" if descending else name), name, descending


def _resolve_order_path_field(model: type, path: str) -> Any:
    """Resolve a (possibly ``__``-traversing) order path to its terminal field.

    Returns ``None`` when any segment fails to resolve, an intermediate
    relation is nullable / reverse / multi-valued, or the terminal is not a
    concrete non-relation column. A non-null terminal behind an optional join
    still yields NULL cursor values, and a to-many join duplicates source rows.
    """
    # In-function import mirrors the file's defensive-Django-imports idiom.
    from django.core.exceptions import FieldDoesNotExist

    current: Any = model
    field: Any = None
    segments = path.split("__")
    for index, segment in enumerate(segments):
        if current is None:
            return None
        resolved_segment = current._meta.pk.name if segment == "pk" else segment
        try:
            field = current._meta.get_field(resolved_segment)
        except FieldDoesNotExist:
            return None
        if index < len(segments) - 1:
            if not getattr(field, "is_relation", False):
                return None
            if relation_kind(field) != "forward_single" or getattr(field, "null", False):
                return None
        current = getattr(field, "related_model", None)
    if field is None or getattr(field, "is_relation", False):
        return None
    if not getattr(field, "concrete", False):
        return None
    return field


def _keyset_order_state(
    state: _KeysetConnectionState,
    queryset: models.QuerySet,
) -> tuple[tuple[CursorColumn, ...], str, models.QuerySet]:
    """Resolve the ROOT slicing state for a keyset queryset's effective order.

    The default-ordered page (the effective order IS the declared
    ``cursor_field`` - what ``_finalize_queryset`` applies when no
    ``orderBy:`` was supplied) reuses the declared columns and fingerprint,
    so root cursors and nested-window cursors are byte-identical by
    construction. An ``orderBy:`` page derives per-order columns instead:
    each effective entry must map to a non-nullable concrete column (local
    or ``__``-related; related values are annotated onto the rows so
    end-cursors can be minted without per-row traversal), and the cursor
    fingerprint pins THIS order - replay under any other order is rejected
    at decode. Entries a value cursor cannot anchor (aggregate aliases,
    expressions, explicit NULLS positioning, nullable columns) raise a
    ``GraphQLError`` naming the keyset boundary rather than paginating
    wrongly.

    Also extends the queryset's ``.only()`` projection with the LOCAL cursor
    columns (the mint reads their attnames off the page rows) - related-path
    values ride their annotations instead.
    """
    effective = tuple(queryset.query.order_by)
    if not effective or effective == state.cursor_field:
        # The declared-order fast path (also the defensive no-order shape:
        # order by the declared cursor_field, the keyset connection default).
        if not effective:
            queryset = queryset.order_by(*state.cursor_field)
        queryset = _extend_only_projection(
            queryset,
            tuple(column.field.attname for column in state.columns),
        )
        return state.columns, state.fingerprint, queryset
    model = state.definition.model
    refs: list[str] = []
    columns: list[CursorColumn] = []
    annotations: dict[str, Any] = {}
    local_attnames: list[str] = []
    for index, entry in enumerate(effective):
        parsed = _keyset_order_ref(entry)
        field = None if parsed is None else _resolve_order_path_field(model, parsed[1])
        if parsed is None or field is None:
            raise GraphQLError(
                "This connection uses keyset cursors (Meta.cursor_field), which "
                "require every ordering entry to be a database column; the "
                "requested order cannot anchor stable cursors. Remove the "
                "unsupported orderBy entry or paginate under the default order.",
            )
        ref, name, descending = parsed
        if getattr(field, "null", False):
            raise GraphQLError(
                "This connection uses keyset cursors (Meta.cursor_field), which "
                f"require non-nullable ordering columns; '{name}' is nullable. "
                "Order by a non-nullable column or paginate under the default "
                "order.",
            )
        if not _is_supported_cursor_field(field):
            raise GraphQLError(
                "This connection uses keyset cursors (Meta.cursor_field), which "
                f"require portable ordering semantics; '{name}' is a JSONField, "
                "whose ordering differs between database backends. Order by a "
                "scalar column or paginate under the default order.",
            )
        if "__" in name:
            value_source = f"_dst_cursor_value_{index}"
            annotations[value_source] = models.F(name)
        else:
            value_source = field.attname
            local_attnames.append(field.attname)
        refs.append(ref)
        columns.append(
            CursorColumn(
                order_ref=ref,
                name=name,
                descending=descending,
                field=field,
                value_source=value_source,
            ),
        )
    if annotations:
        queryset = queryset.annotate(**annotations)
    queryset = _extend_only_projection(queryset, tuple(local_attnames))
    return tuple(columns), order_fingerprint(tuple(refs)), queryset


@dataclass(frozen=True)
class _KeysetPage:
    """One fetched keyset page plus the spec-algorithm pageInfo inputs."""

    rows: list[Any]
    overfetched: bool
    backward: bool
    after_supplied: bool
    before_supplied: bool
    # ``last: 0`` mirrors Strawberry's ``edges[-0:]`` serve-all quirk: the
    # offset ``ListConnection`` path overwrites ``hasPreviousPage`` from
    # "did ``edges[-last:]`` trim?" which is always False for ``last == 0``.
    # Without this flag a keyset ``last: 0`` + ``after:`` page would report
    # ``hasPreviousPage`` from ``after_supplied`` and diverge from the offset
    # connection on the same arguments.
    last_zero_quirk: bool = False

    @property
    def has_next_page(self) -> bool:
        """Relay's ``HasNextPage`` in the value domain.

        The forward overfetch answers it data-driven; otherwise "``before``
        was supplied" does - a supplied ``before`` cursor positions at
        extant row values, the same MAY-semantics the offset pipeline's
        ``start > 0`` arithmetic encodes for ``hasPreviousPage``.
        """
        return (not self.backward and self.overfetched) or self.before_supplied

    @property
    def has_previous_page(self) -> bool:
        """Relay's ``HasPreviousPage``: the backward overfetch, else "``after`` was supplied".

        ``last: 0`` is the exception: Strawberry's serve-all quirk never trims,
        so ``hasPreviousPage`` stays False even when ``after`` advanced the
        materialized window (byte parity with offset ``ListConnection``).
        """
        if self.last_zero_quirk:
            return False
        return (self.backward and self.overfetched) or self.after_supplied


def _resolve_keyset_connection(
    cls: type,
    nodes: Any,
    *,
    info: Info,
    want_count: bool,
    state: _KeysetConnectionState,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    max_results: int | None = None,
    **kwargs: Any,
) -> Any:
    """The framework-owned slicer for KEYSET (``Meta.cursor_field``) connections.

    Serves every non-window keyset path - root connections AND the
    per-parent fallback pipeline - through the one canonical codec, so a
    cursor minted anywhere replays everywhere (the cross-strategy parity
    invariant). Strawberry's ``ListConnection`` is never reached for a
    keyset connection: it speaks only the offset ``arrayconnection``
    vocabulary.

    The Relay pagination algorithm, in the value domain:

    1. Resolve the effective-order cursor columns (``_keyset_order_state``);
       capture the PRE-seek queryset as the ``totalCount`` source (Relay's
       "count of the pre-pagination set" - the seek IS pagination).
    2. Apply the ``after:`` / ``before:`` seeks (they compose). The queryset
       arriving here is ALREADY visibility-scoped (the pipeline ran
       ``get_queryset`` / cascade permissions / filters first), so the
       decode filter inherits the viewer's visibility by construction - a
       cursor minted under one viewer replays under another without leaking
       rows (the permission-aware-decode contract).
    3. Fetch page+1: forward for ``first`` (or the ``relay_max_results`` cap
       when neither bound is given - ``ListConnection`` parity), through the
       REVERSED order for ``last``-only (restored to forward order in
       memory). The overfetch answers the data-driven page flag; the spec's
       cursor-supplied rules answer the opposite one (``_KeysetPage``).

    Sync/async dispatch mirrors ``ListConnection.resolve_connection``: a
    sync field materializes the lazy queryset in the resolver's context; an
    async field receives a coroutine that iterates with the async engine
    and counts via ``acount``.
    """
    if not isinstance(nodes, models.QuerySet):
        raise GraphQLError(
            "This connection uses keyset cursors (Meta.cursor_field), which "
            "seek and mint from database rows; the connection resolver must "
            "return a QuerySet (or a Manager), not a plain iterable.",
        )
    _guard_source_not_pre_sliced(nodes)
    columns, fingerprint, queryset = _keyset_order_state(state, nodes)
    count_source = queryset
    if after is not None:
        cursor = decode_keyset_cursor(after, columns, fingerprint=fingerprint, argument="after")
        queryset = queryset.filter(KeysetSeek(columns=columns, cursor=cursor).q())
    if before is not None:
        cursor = decode_keyset_cursor(before, columns, fingerprint=fingerprint, argument="before")
        queryset = queryset.filter(KeysetSeek(columns=columns, cursor=cursor, flip=True).q())
    cap = resolve_relay_max_results(info, max_results)
    for argument, value in (("first", first), ("last", last)):
        if isinstance(value, int):
            # SliceMetadata's exact validation text, so a keyset connection's
            # pagination errors do not fork from the offset vocabulary's.
            if value < 0:
                raise ValueError(f"Argument '{argument}' must be a non-negative integer.")
            if value > cap:
                raise ValueError(f"Argument '{argument}' cannot be higher than {cap}.")
    last_zero_quirk = (
        isinstance(last, int) and last == 0 and not isinstance(first, int) and before is None
    )
    backward = isinstance(last, int) and not isinstance(first, int) and not last_zero_quirk
    # Strawberry's ``edges[-0:]`` quirk means ``last: 0`` serves the rows it
    # materialized. Preserve that compatibility, but never let the quirk bypass
    # the connection's existing Relay cap: fetch at most ``cap + 1`` so the
    # returned page stays bounded and ``hasNextPage`` remains data-driven.
    page_size = (
        cap
        if last_zero_quirk
        else (last if backward else (first if isinstance(first, int) else cap))
    )
    fetch_queryset = queryset.reverse() if backward else queryset
    fetch_limit = page_size + 1

    if not should_resolve_list_connection_edges(info):
        # ``ListConnection`` parity: nothing under ``edges`` / ``pageInfo``
        # is selected, so no row is fetched and the placeholder flags are
        # inert. ``totalCount`` is its own sibling selection and still
        # counts when requested.
        conn = cls(
            edges=[],
            page_info=relay.PageInfo(
                start_cursor=None,
                end_cursor=None,
                has_previous_page=False,
                has_next_page=False,
            ),
        )
        if want_count and isinstance(nodes, (AsyncIterator, AsyncIterable)) and in_async_context():

            async def _resolve_count_only_async() -> Any:
                return _set_total_count(
                    conn,
                    want_count=True,
                    value=await count_source.acount(),
                )

            return _resolve_count_only_async()
        return _set_total_count(conn, want_count=want_count, value=count_source.count)

    def _build(page: _KeysetPage, total: Any) -> Any:
        rows = page.rows[:page_size] if page.overfetched else page.rows
        if page.backward:
            rows = list(reversed(rows))
        edge_class = _window_edge_class(cls)
        edges = [
            edge_class(
                node=cls.resolve_node(row, info=info, **kwargs),
                cursor=encode_keyset_cursor(columns, row, fingerprint=fingerprint),
            )
            for row in rows
        ]
        conn = cls(
            edges=edges,
            page_info=relay.PageInfo(
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
                has_previous_page=page.has_previous_page,
                has_next_page=page.has_next_page,
            ),
        )
        return _set_total_count(conn, want_count=want_count, value=total)

    def _page(rows: list[Any]) -> _KeysetPage:
        return _KeysetPage(
            rows=rows,
            overfetched=len(rows) == fetch_limit,
            backward=backward,
            after_supplied=after is not None,
            before_supplied=before is not None,
            last_zero_quirk=last_zero_quirk,
        )

    if isinstance(nodes, (AsyncIterator, AsyncIterable)) and in_async_context():

        async def _resolve_async() -> Any:
            source = fetch_queryset[:fetch_limit]
            rows = [row async for row in source]
            total = await count_source.acount() if want_count else None
            return _build(_page(rows), total)

        return _resolve_async()

    return _build(
        _page(list(fetch_queryset[:fetch_limit])),
        count_source.count() if want_count else None,
    )


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
    A node-level ``totalCount`` deep inside ``edges { node { ... } }`` must not
    make the OUTER connection's predicate fire (a spurious ``COUNT`` and, on a
    non-queryset source, a spurious M1-guard raise).

    Delegates the whole walk to the shared per-selection primitive
    ``optimizer/selections.py::connection_total_count_selected`` - the SAME
    implementation the plan-time ``connection_count_required`` uses - so the
    resolve-time count detection cannot drift from the optimizer's plan-time
    predicate (the conditional ``_dst_total_count`` contract's invariant).
    """
    return any(
        connection_total_count_selected(selected_field) for selected_field in info.selected_fields
    )


def _has_next_page_requested(info: Info) -> bool:
    """Return whether the query selects ``pageInfo { hasNextPage }``.

    The ``hasNextPage`` sibling of ``_total_count_requested``: the window fast
    path derives ``hasNextPage`` either from a conditional partition count or
    from the count-free n+1 probe used by a plain ``first: N`` page. When a
    non-probe window arrives without a required count or keyset-seek annotation,
    ``_resolve_from_window`` consults this predicate to distinguish observable
    plan drift (defensive per-parent fallback) from an inert placeholder flag.
    Delegates the whole walk to the shared per-selection primitive
    ``optimizer/selections.py::connection_has_next_page_selected`` - the same
    implementation the plan-time ``connection_count_required`` uses - so the
    two halves cannot drift independently.
    """
    return any(
        connection_has_next_page_selected(selected_field)
        for selected_field in info.selected_fields
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
    object straight from the windowed-prefetch row-number, conditional-count,
    keyset-seek, and probe shape. Planned marker rows directly serve ``first: 0``
    and overshot ``after:`` empty pages; the wrapper's callable is reserved for
    genuine defensive recovery.

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
    dispatches keyset sources to the framework slicer or delegates an ordinary
    offset source to its ``ListConnection`` ``super().resolve_connection`` path.
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
    """Generic Relay connection base owning package pagination dispatch.

    Adds the Decision-3 ``first`` + ``last`` guard, consumes optimized nested
    windows, and dispatches ``Meta.cursor_field`` sources to the framework-owned
    keyset slicer. Ordinary non-window offset sources still delegate cursor
    encoding, ``pageInfo``, edge wrapping, and slicing to
    ``strawberry.relay.ListConnection``. The base carries no ``total_count``
    field; that is the opt-in ``<TypeName>Connection`` variant's job (Decision 4).
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
        """Guard pagination, consume optimized windows, then dispatch by cursor mode.

        The fast path (Decision 5): after the guard and before Strawberry's list
        slicing, detect the internal ``_WindowedConnectionRows`` wrapper the
        synthesized relation-connection resolver returns when the walker's
        windowed prefetch fired, and build the Relay object straight from the
        row-number, conditional-count, keyset-seek, or probe annotations - one
        window query for every parent's page, zero per-parent queries. Planned
        marker rows directly serve empty ``first: 0`` and overshot ``after:``
        pages. Non-window keyset sources use the package's codec-aware slicer;
        only ordinary offset sources fall through to ``ListConnection``.
        Correctness never depends on a plan having fired. The through-schema
        tests are mandatory because ``ConnectionExtension.resolve`` wraps the
        resolver.
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
        keyset_state = _keyset_connection_context(cls)
        if keyset_state is not None:
            # Keyset-mode (Meta.cursor_field): root and per-parent-fallback
            # slicing is framework-owned - ``ListConnection`` cannot decode
            # or mint value cursors.
            return _resolve_keyset_connection(
                cls,
                nodes,
                info=info,
                want_count=False,
                state=keyset_state,
                before=before,
                after=after,
                first=first,
                last=last,
                max_results=max_results,
                **kwargs,
            )
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


register_subsystem_clear(clear_connection_type_cache, owner="connection.type_cache")


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

    def _populate(namespace: dict) -> None:
        # The node type rides the generated class (no annotation, so
        # Strawberry never surfaces it) - the keyset-mode resolution
        # (``_keyset_connection_context``) reads the target's
        # ``Meta.cursor_field`` through it at resolve time.
        namespace["_dst_node_type"] = target_type
        if populate is not None:
            populate(namespace)

    generated = types.new_class(
        f"{definition.graphql_type_name}Connection",
        (DjangoConnection[target_type],),
        exec_body=_populate,
    )
    return strawberry.type(generated, description=description)


def _build_total_count_connection(target_type: type) -> type:
    """Generate the concrete ``<TypeName>Connection`` carrying ``totalCount``.

    The generated class subclasses ``DjangoConnection[target_type]`` (so it
    inherits the ``first`` + ``last`` guard), declares a ``total_count`` field
    whose resolver reads a private instance attribute, and overrides
    ``resolve_connection`` to attach the post-filter pre-slice count ONLY when
    ``totalCount`` is in the selection set. Optimized windows read the count
    annotation, keyset pages count through the framework slicer, and ordinary
    non-window offset querysets use sync ``.count()`` / async ``.acount()`` before
    or after delegating slicing to the base (Decision 4).
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
        # ``.count()`` entirely (Decision 5). Marker rows directly serve planned
        # ``limit == 0`` / overshot-``offset`` pages with their true count and
        # flags; only unservable wrappers such as ``last: 0`` or required-
        # annotation drift recover through the per-parent pipeline. Pins:
        # ``test_fast_path_total_count_marker_bypasses_non_queryset_guard`` /
        # ``test_fast_path_ambiguous_empty_served_from_marker_row`` /
        # ``test_fast_path_last_zero_quirk_parity_via_fallback``.
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
        keyset_state = _keyset_connection_context(cls)
        if keyset_state is not None:
            # Keyset-mode: the framework slicer owns slicing AND the count
            # attach (its ``count_source`` is the same pre-pagination
            # queryset the attach helpers would count; keeping both inside
            # the slicer spares the M1 non-queryset guard a second raise
            # site - the slicer's own QuerySet guard already covers it).
            return _resolve_keyset_connection(
                cls,
                nodes,
                info=info,
                want_count=want_count,
                state=keyset_state,
                before=before,
                after=after,
                first=first,
                last=last,
                max_results=max_results,
                **kwargs,
            )
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
    # The bound ``.count`` is passed lazily: ``_set_total_count`` only calls
    # it when the count was requested (no COUNT query otherwise).
    return _set_total_count(conn, want_count=want_count, value=nodes.count)


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
        # The ``await`` keeps this step explicitly colored (the package's
        # sync/async convention); the attr write itself still routes through
        # the single ``_set_total_count`` writer.
        _set_total_count(conn, want_count=True, value=await nodes.acount())
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
    cursor_field = getattr(
        getattr(target_type, "__django_strawberry_definition__", None),
        "cursor_field",
        None,
    )
    explicit = tuple(qs.query.order_by)
    if cursor_field is not None and not explicit:
        # Keyset-mode default order: the declared ``cursor_field`` IS the
        # connection order (the BACKLOG "enforced matching order" contract) -
        # it beats model ``Meta.ordering``, whose columns the cursors do not
        # encode. It is finalization-validated to end in a unique column, so
        # it is already a total order. An explicit ``orderBy:`` (a non-empty
        # ``query.order_by``) keeps the shipped derivation below; the keyset
        # slicer then fingerprints THAT order into its cursors.
        return apply_connection_optimization(target_type, qs.order_by(*cursor_field), info)
    effective = explicit or tuple(target_model._meta.ordering)
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

    Awaitable sources are rejected before normalization. They can only come
    from a plain ``def`` consumer resolver that returns an awaitable, a shape
    committed to this sync path at field construction. The list field enforces
    the same boundary through ``post_process_queryset_result_sync``.
    """
    definition = target_type.__django_strawberry_definition__
    reject_awaitable_sync_source(source, target_type)
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
    """Async sibling of ``_pipeline_sync`` - awaits the colored visibility / filter / order steps.

    The consumer ``resolver=`` return was already awaited once by
    ``_build_connection_resolver``'s async branch, so a value that is STILL
    awaitable here is a nested async resolver whose inner awaitable would
    otherwise pass the non-queryset sidecar guard and skip visibility entirely.
    The shared ``reject_residual_async_source`` guard (the same one the list
    field's ``post_process_queryset_result_async`` applies) fails it closed
    before ``_prepare_pipeline_source`` can treat it as a plain iterable.
    """
    definition = target_type.__django_strawberry_definition__
    reject_residual_async_source(source, target_type)
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
    rows to probe and is still a conclusive planned window candidate: marker
    shapes retain row 1 whenever the parent has children, so an empty list means
    the parent genuinely has none. ``resolve_connection`` still owns the slice-
    aware page and flag construction.
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
    the fast path). Divergent aliases (idea #2) land one window PER RESPONSE
    KEY under ``_dst_<field>$<key>_connection`` instead, so the resolver
    probes the per-key attr FIRST - derived from ``info.path.key``, the same
    response-key vocabulary the walker planned under (the resolver cannot see
    the pagination arguments to re-derive the window;
    ``ConnectionExtension`` consumes them) - then falls back to the shared
    legacy attr. When the found rows carry the window annotations AND the
    resolver's own ``filter`` / ``order_by`` kwargs are absent, it returns a
    ``_WindowedConnectionRows`` marker handing the rows to the generated
    connection class (which builds the Relay object - the resolver never
    constructs a connection, since Strawberry feeds the resolver return back
    through ``resolve_connection`` as the node iterable). A sidecar kwarg
    present means the window is ignored and the pipeline runs, so a future
    planner/argument desync can never serve unfiltered wrong data. The marker
    also carries a fallback factory re-running this pipeline as a defensive
    recovery seam when the wrapper cannot be served (for example ``last: 0``, a
    backward keyset wrapper, or required-annotation drift). Planned ``first: 0``
    and overshot ``after:`` marker pages are served directly. The resolver never
    sees the pagination arguments - ``ConnectionExtension`` consumes them.

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
        # Per-response-key window first (divergent aliases, idea #2): the attr
        # is a pure function of ``info.path.key`` - the resolve-time twin of
        # the response key the walker planned under. ``probe_attr`` tracks
        # which attr actually held rows so the strictness probe below reads
        # the same location the fast path did; with neither attr present it
        # stays the shared attr, whose absence IS the unplanned signal.
        per_key_attr = _relation_connection_to_attr_for_key(relation_field_name, info.path.key)
        probe_attr = per_key_attr
        window_rows = getattr(root, per_key_attr, None)
        if window_rows is None:
            probe_attr = to_attr
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
            # can recover this per-parent pipeline if defensive window
            # validation finds the wrapper unservable. Normal marker-only empty
            # pages are served directly and do not call the factory.
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
            to_attr=probe_attr,
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
