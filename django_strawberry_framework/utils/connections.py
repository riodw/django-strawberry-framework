"""Connection planner/resolver shared contracts: window bounds + sidecar kwargs.

A cycle-safe home for two correctness contracts that the optimizer planner
(``optimizer/walker.py``) and the Relay resolver (``connection.py``) must spell
IDENTICALLY, or optimizer-on and optimizer-off behavior can split:

* The slice-window derivation (``derive_connection_window_bounds`` /
  ``ConnectionWindowBounds``) - the walker decides which rows to prefetch into a
  window; the resolver later decides whether the annotated rows can be consumed
  and how to compute cursors / page flags. Both derive ``(offset, limit,
  reverse)`` from the same ``SliceMetadata.from_arguments`` engine and the same
  reverse / limit rule, so the resolve-time window matches the plan-time window
  by construction (spec-033 Decision 4 / Decision 5, the cursor-parity
  invariant's resolve-time half).
* The connection sidecar kwarg family (``CONNECTION_SIDECAR_KWARGS`` and the
  presence predicates) - the walker refuses to window-plan a sidecar-bearing
  nested connection, and the resolver refuses to consume a window when sidecar
  kwargs are present (spec-032 Decision 6). Those two decisions must always use
  the same kwarg family; a future sidecar (e.g. ``search``) is then a one-line
  edit here rather than synchronized edits across the planner and resolver.

This module depends on neither ``connection.py`` nor ``optimizer/walker.py`` so
both can import it without a cycle. Plan-time argument coercion (an inline Int
literal arrives as a token STRING; a Strawberry resolver argument is already
``int``) is deliberately NOT owned here - it is the walker's concern and stays
in ``optimizer/walker.py::_coerce_pagination_int``; this helper assumes its
``first`` / ``last`` are already the values ``SliceMetadata`` will gate on.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any

from strawberry.relay.utils import SliceMetadata

from ..exceptions import OptimizerError

# The connection sidecar argument names, in BOTH vocabularies the shared
# readers below see. ``CONNECTION_ORDER_KWARG`` is the PYTHON kwarg name (the
# key in the resolver ``**kwargs``); Strawberry's default ``auto_camel_case``
# renders it as the ``orderBy`` GraphQL argument, and the walker's converted
# ``sel.arguments`` carry the RAW GraphQL name (``convert_arguments`` keeps
# ``node.name.value`` verbatim) - so the plan-time sidecar predicate must
# recognize the camel spelling too, or an ``orderBy:``-bearing nested
# connection window-plans a DEAD window (the resolver's own sidecar gate
# refuses it and runs per-parent) and its recorded identity hides the
# fallback from strictness. ``filter`` is spelled identically in both
# vocabularies, which is why only the order kwarg needs the twin.
CONNECTION_FILTER_KWARG = "filter"
CONNECTION_ORDER_KWARG = "order_by"
CONNECTION_ORDER_KWARG_GRAPHQL = "orderBy"
CONNECTION_SIDECAR_KWARGS = (CONNECTION_FILTER_KWARG, CONNECTION_ORDER_KWARG)


class UnwindowableConnection(Exception):  # noqa: N818 - control-flow signal, not a surfaced error
    """Internal signal: this pagination shape cannot be served by a windowed prefetch.

    Raised by ``derive_connection_window_bounds`` when Strawberry's Python-slice
    metadata cannot be represented by the SQL row-number window without changing
    results or page flags. This includes offset-bearing backward windows
    (``after`` + ``last``) and inverted ``after`` + ``before`` intervals. Per
    spec-033 Decision 5 these valid shapes fall back per parent rather than being
    approximated. Malformed negative cursor indices raise ``TypeError`` instead,
    preserving the existing pagination-error locality path.

    A control-flow sentinel, deliberately NOT a ``DjangoStrawberryFrameworkError``
    and NOT a ``ValueError`` / ``TypeError``: the walker catches the pagination
    *errors* (``ValueError`` / ``TypeError``) to leave a selection unplanned while
    still recording the field as accounted-for (it will raise its OWN error), but
    must treat THIS shape as a fully-unplanned Decision-6 fallback (no
    ``planned_resolver_keys`` entry) so the per-parent access stays visible to the
    Slice-4 strictness contract. A distinct type keeps the two paths separable.
    """


def connection_sidecar_inputs_from_kwargs(kwargs: dict[str, Any]) -> tuple[Any, Any]:
    """Extract ``(filter_input, order_by_input)`` from a kwargs/arguments dict.

    The single reader of the sidecar kwarg keys so no caller re-spells
    ``kwargs.get("filter")`` / ``kwargs.get("order_by")``. Reads BOTH order
    spellings because its two callers speak different vocabularies: the
    resolver passes Python ``**kwargs`` (``order_by``), the walker passes the
    converted selection's RAW GraphQL argument names (``orderBy`` under the
    default ``auto_camel_case``; ``order_by`` when camelization is disabled).
    No collision is possible - the resolver's kwargs never carry the camel
    key, and on the walker side either spelling IS the sidecar argument.
    """
    order_by_input = kwargs.get(CONNECTION_ORDER_KWARG)
    if order_by_input is None:
        order_by_input = kwargs.get(CONNECTION_ORDER_KWARG_GRAPHQL)
    return kwargs.get(CONNECTION_FILTER_KWARG), order_by_input


def has_connection_sidecar_input(*, filter_input: Any, order_by_input: Any) -> bool:
    """Return whether either already-extracted sidecar input is present."""
    return filter_input is not None or order_by_input is not None


def has_connection_sidecar_kwargs(kwargs: dict[str, Any]) -> bool:
    """Return whether a kwargs/arguments dict carries any sidecar input.

    The walker's fallback predicate (a sidecar-bearing nested connection is not
    window-planned) and the resolver's "no sidecar" gate share this one rule.
    """
    filter_input, order_by_input = connection_sidecar_inputs_from_kwargs(kwargs)
    return has_connection_sidecar_input(filter_input=filter_input, order_by_input=order_by_input)


def is_ambiguous_empty_window(offset: int, limit: int | None, *, reverse: bool = False) -> bool:
    """Whether this window shape can produce an AMBIGUOUS empty page.

    ``offset > 0`` (an overshot ``after:``) and ``limit == 0`` (``first: 0``)
    both yield an empty page for a parent whose children all sit outside the
    range AND for a parent with no children at all - historically forcing a
    per-parent fallback. Workstream C disambiguates these shapes with marker
    rows; reversed (``last``-only) windows never plan markers.

    The plan-time/resolve-time contract shared - like the sidecar-kwarg family
    above - by everything that must agree on "ambiguous": the window builders
    that ADD the marker rows (``plans.py::window_range_plan``, feeding both
    ``apply_window_pagination`` and the lateral SQL), the walker's forced
    ``with_total_count`` for these shapes, and the resolver that CONSUMES rows
    as marker-classified (``connection.py::_resolve_from_window``). One
    predicate so the plan side and the consume side cannot drift.
    """
    return not reverse and (offset > 0 or limit == 0)


@dataclass(frozen=True)
class WindowRangePlan:
    """The pure window-range decisions one ``(offset, limit, reverse)`` slice implies.

    Shared by the ORM window renderer and lateral SQL renderer so bounds,
    marker rows, and count requirements cannot drift. ``limit`` is normalized
    (Relay's ``sys.maxsize`` sentinel becomes ``None`` = no upper bound);
    ``lower_bound`` is the exclusive forward-row-number floor; ``upper_bound``
    is the inclusive ceiling; ``add_marker_rows`` keeps each partition's row 1
    for ambiguous empty-window shapes; ``plain_first_page`` marks the
    unambiguous ``first: N`` shape a renderer may express as plain
    ``ORDER BY``/``LIMIT``; ``requires_total_count`` marks windows whose
    resolution needs the partition count regardless of the selected fields.

    ``next_page_probe`` marks the count-free ``hasNextPage`` overfetch (the
    n+1 probe): a ``plain_first_page`` window that fetches ONE sentinel row
    past the page so ``hasNextPage`` is answered by the sentinel's presence
    instead of a ``COUNT(1) OVER (PARTITION BY ...)`` that scans the whole
    partition. It is honored only on the ``plain_first_page`` shape (every
    other shape already needs the count for an independent reason), so it and
    ``add_marker_rows`` are mutually exclusive by construction. The ``+1``
    sentinel arithmetic lives in exactly one place - the ``_probe_increment``
    primitive that both ``fetch_upper_bound`` and ``fetch_limit`` add to the
    derived bounds the renderers read UNCONDITIONALLY; ``upper_bound`` /
    ``limit`` keep their PAGE semantics (the resolver's split and the marker
    predicate depend on that). The plan-time decision is
    ``wants_next_page_probe``, the pure
    predicate the walker calls; the resolver does NOT re-derive it from the
    selection (same-argument aliases share one window whose shape was fixed
    from the MERGED selection, so a per-alias re-derivation would drift) - it
    reads the probe off the window's physical shape instead
    (``connection.py::_resolve_from_window``).
    """

    offset: int
    limit: int | None
    reverse: bool
    lower_bound: int | None
    upper_bound: int | None
    add_marker_rows: bool
    plain_first_page: bool
    requires_total_count: bool
    next_page_probe: bool = False

    @property
    def _probe_increment(self) -> int:
        """The sentinel-row count the probe adds to a fetch bound (1 iff probing).

        The single owner of the n+1 arithmetic: ``fetch_upper_bound`` and
        ``fetch_limit`` both add THIS instead of each spelling their own ``+1``,
        so the sentinel policy has one place to change and the two bounds cannot
        drift. Zero when the probe is off, so both bounds equal their page
        semantics by construction.
        """
        return 1 if self.next_page_probe else 0

    @property
    def fetch_upper_bound(self) -> int | None:
        """The inclusive row-number ceiling to FETCH (page bound plus the probe sentinel).

        Equals ``upper_bound`` whenever the probe is off (``_probe_increment`` is
        zero), so every existing renderer call site and test is untouched by
        construction; adds the one sentinel row for the probe shape.
        """
        if self.upper_bound is None:
            return None
        return self.upper_bound + self._probe_increment

    @property
    def fetch_limit(self) -> int | None:
        """The plain-first-page in-branch ``LIMIT`` to FETCH (page size plus the probe sentinel).

        The lateral fast branch reads this instead of ``limit``; equal to
        ``limit`` when the probe is off (shares ``_probe_increment`` with
        ``fetch_upper_bound``).
        """
        if self.limit is None:
            return None
        return self.limit + self._probe_increment

    def wants_next_page_probe(self, *, has_next_selected: bool, total_selected: bool) -> bool:
        """Whether this window should serve ``hasNextPage`` from an overfetch probe.

        True only for the ``plain_first_page`` shape (``first: N`` from the
        start) when ``pageInfo.hasNextPage`` is selected and ``totalCount`` is
        NOT: the sentinel row answers ``hasNextPage`` without the per-partition
        count. Every other shape already forces the count (ambiguous /
        unbounded / reversed windows via ``requires_total_count``, or a
        genuinely-observable ``totalCount``), so the internal
        ``plain_first_page`` re-check makes this self-normalizing and safe to
        call on any plan.

        The single implementation of the PLAN-time probe decision, called by
        ``walker.py::_plan_connection_relation`` (feeding ``has_next_selected``
        / ``total_selected`` from the ``optimizer/selections.py`` walks over
        the merged selection). The resolver deliberately does NOT call this:
        same-argument aliases share one window planned from the MERGED
        selection, so re-deriving per alias from each response key's ``info``
        would drift from the shared shape.
        ``connection.py::_resolve_from_window`` instead reads the probe off the
        window's physical shape (a ``plain_first_page`` window carrying no
        ``_dst_total_count`` annotation), which IS this decision materialized -
        sound because the walker keeps ``next_page_probe`` and
        ``with_total_count`` mutually exclusive.
        """
        return self.plain_first_page and has_next_selected and not total_selected


def window_range_plan(
    *,
    offset: int,
    limit: int | None,
    reverse: bool,
    next_page_probe: bool = False,
    keyset_counted: bool = False,
) -> WindowRangePlan:
    """Resolve one slice window into its shared ``WindowRangePlan``.

    Pure and renderer-agnostic. Owns the two sentinel rules spelled once for
    every consumer:

    - ``limit is None`` OR Relay's ``sys.maxsize`` means "no upper bound"
      (the offset floor still applies). Normalized here so no renderer ever
      sees ``sys.maxsize``.
    - A negative limit is an invalid internal window specification and raises
      ``OptimizerError``. Pagination shapes that Strawberry maps to a negative
      ``expected`` are classified upstream by
      ``derive_connection_window_bounds`` and fall back per parent; silently
      treating a negative direct-call limit as unbounded would recreate the same
      wrong-row failure in both renderers.
    - A negative offset likewise raises ``OptimizerError``. Derived offset-cursor
      starts are classified as malformed pagination upstream, but direct request
      objects must not turn one into an absolute SQL row-number floor.

    ``next_page_probe`` (the count-free ``hasNextPage`` overfetch) is honored
    only on the ``plain_first_page`` shape and ignored everywhere else, so a
    caller may pass the raw decision through without re-checking the shape and
    the ``add_marker_rows`` / ``next_page_probe`` fields stay mutually
    exclusive by construction.

    ``keyset_counted`` marks the COUNTED keyset-seek window (a ``cursor_field``
    connection resolving ``after:`` with an observable count): its row numbers
    are PAGE-RELATIVE (a filtered running count - pre-seek rows carry 0), so
    the window keeps an EXCLUSIVE FLOOR at row 0 (``lower_bound = offset``
    even when the offset is 0) and its empty page is AMBIGUOUS exactly like
    an overshot ``after:`` offset (a parent whose children all precede the
    cursor vs a childless parent) - so it plans marker rows, which the
    renderers express as the partition's ABSOLUTE first row. The count-free
    keyset shape puts the seek in the base WHERE instead (its rows number
    1..N natively) and never sets this flag.
    """
    if offset < 0:
        raise OptimizerError("A connection window offset cannot be negative.")
    if limit is not None and limit < 0:
        raise OptimizerError("A connection window limit cannot be negative.")
    if limit == sys.maxsize:
        limit = None
    lower_bound = offset if (offset or keyset_counted) else None
    bounded = limit is not None
    upper_bound = (limit if reverse else offset + limit) if bounded else None
    ambiguous = keyset_counted or is_ambiguous_empty_window(offset, limit, reverse=reverse)
    plain_first_page = not reverse and offset == 0 and bounded and limit > 0
    return WindowRangePlan(
        offset=offset,
        limit=limit,
        reverse=reverse,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        add_marker_rows=ambiguous and (lower_bound is not None or upper_bound is not None),
        plain_first_page=plain_first_page,
        requires_total_count=ambiguous or limit is None,
        next_page_probe=next_page_probe and plain_first_page and not keyset_counted,
    )


def assert_window_fetch_mode(range_plan: WindowRangePlan, *, with_total_count: bool) -> None:
    """Enforce the probe/count mutual-exclusion contract on a RESOLVED window plan.

    The count-free ``hasNextPage`` probe (``range_plan.next_page_probe``, already
    normalized by ``window_range_plan`` to the ``plain_first_page`` shape) fetches
    one sentinel row past the page and answers ``hasNextPage`` from its presence.
    A window that engages the probe must NOT also annotate the partition count:
    the resolver infers "no probe" from a present ``_dst_total_count`` and would
    pass the n+1 sentinel through as a real edge
    (``connection.py::_resolve_from_window``). The invariant is the EFFECTIVE
    state, not the raw flags - a ``next_page_probe`` request off the plain-first-page
    shape is inert (``window_range_plan`` drops it), so it may coexist with the
    count harmlessly and is not rejected here.

    The single owner of the boundary check every window entry point shares
    (``plans.py::apply_window_pagination`` for the ORM window,
    ``nested_fetch.py::NestedConnectionRequest`` and
    ``lateral_fetch.py::LateralWindowSpec`` at construction). Raises the loud
    ``OptimizerError`` - never silently normalizes one flag - so a planner or
    strategy bug surfaces at its origin instead of corrupting a page. It is not a
    ``ValueError`` / ``TypeError``, so the walker's leave-unplanned pagination
    handler cannot swallow it.
    """
    if with_total_count and range_plan.next_page_probe:
        raise OptimizerError(
            "A count-free hasNextPage probe window (next_page_probe) cannot also "
            "annotate the partition count (with_total_count): the resolver would "
            "pass the overfetched sentinel row through as a real edge. These fetch "
            "modes are mutually exclusive.",
        )


def assert_window_fetch_mode_for(
    *,
    offset: int,
    limit: int | None,
    reverse: bool,
    with_total_count: bool,
    next_page_probe: bool,
) -> None:
    """``assert_window_fetch_mode`` for callers holding RAW window arguments.

    The request objects (``NestedConnectionRequest`` / ``LateralWindowSpec``)
    carry ``(offset, limit, reverse, next_page_probe)`` rather than a resolved
    ``WindowRangePlan``; this resolves the plan through the shared
    ``window_range_plan`` and delegates, so the effective-state rule is spelled
    exactly once.
    """
    assert_window_fetch_mode(
        window_range_plan(
            offset=offset,
            limit=limit,
            reverse=reverse,
            next_page_probe=next_page_probe,
        ),
        with_total_count=with_total_count,
    )


def split_window_rows(
    rows: list[Any],
    range_plan: WindowRangePlan,
    *,
    row_number: str,
) -> tuple[list[Any], bool]:
    """Split annotated window ``rows`` into page rows and dropped sentinel rows.

    Returns ``(page_rows, probe_row_seen)``. The one home for sentinel-row
    exclusion, owning BOTH sentinel shapes the window may carry - and they are
    mutually exclusive (a window is ``add_marker_rows`` XOR ``next_page_probe``
    XOR neither):

    - ``add_marker_rows`` (the ambiguous ``after:`` / ``first: 0`` shapes,
      workstream C): each partition's row 1 is kept as a marker so an empty
      page and a childless parent stay distinguishable. The page proper is the
      rows past the offset (``limit == 0`` has no page at all); ``probe_row_seen``
      is ``False`` (markers do not signal a next page).
    - ``next_page_probe`` (the count-free ``hasNextPage`` overfetch): the window
      fetched one row past the page (``rn == upper_bound + 1``). The page is the
      rows up to ``upper_bound``; ``probe_row_seen`` reports whether the sentinel
      was present, which IS ``hasNextPage`` - no ``_dst_total_count`` needed.

    Render-agnostic: works identically for the ORM window and the lateral SQL
    because both keep FORWARD row numbers and the lateral fast branch computes
    ``rn`` BEFORE its ``LIMIT`` applies, so the sentinel is always the
    ``rn == upper_bound + 1`` row regardless of which renderer produced it.
    This helper plus the ``hasNextPage`` derivation in
    ``connection.py::_resolve_from_window`` are the resolve-side surface a
    future keyset-cursor backend (which makes ``rn`` page-relative) has to
    touch - everything else consumes ``(page_rows, probe_row_seen)`` unchanged.
    """
    if range_plan.add_marker_rows:
        if range_plan.limit == 0:
            return [], False
        return [row for row in rows if getattr(row, row_number) > range_plan.offset], False
    if range_plan.next_page_probe and range_plan.upper_bound is not None:
        page_rows = [row for row in rows if getattr(row, row_number) <= range_plan.upper_bound]
        return page_rows, len(page_rows) < len(rows)
    return list(rows), False


@dataclass(frozen=True)
class ConnectionWindowBounds:
    """The slice window ``(offset, limit, reverse)`` derived from pagination args.

    ``limit is None`` means no upper bound (a forward window with no ``first``);
    ``reverse`` marks the ``last``-only backward window whose bound is the literal
    ``last`` rather than the unbounded ``SliceMetadata.expected``.
    """

    offset: int
    limit: int | None
    reverse: bool


def derive_connection_window_bounds(
    info: Any,
    *,
    before: Any,
    after: Any,
    first: Any,
    last: Any,
    max_results: int | None,
) -> ConnectionWindowBounds:
    """Derive the window ``(offset, limit, reverse)`` from pagination arguments.

    Owns the ``reverse`` predicate and the ``limit`` rule (the cursor-parity
    contract), running the arguments through Strawberry's
    ``SliceMetadata.from_arguments`` - the same engine both the plan-time walker
    and the resolve-time pipeline use. ``max_results`` is passed EXPLICITLY (the
    walker's graphql-core ``info.schema`` has no ``.config`` for the engine to
    read), so the plan-time and resolve-time caps are the same number.

    ``SliceMetadata.from_arguments`` raises ``ValueError`` (negative / over-max
    ``first`` / ``last``) or ``TypeError`` (malformed cursor) for invalid
    pagination; this helper lets those propagate. The walker catches them to
    leave the selection unplanned (Decision 4 step f); the resolver lets them
    surface as the field's own pagination error.

    Backward (``last``-only) pagination needs the reversed-row-number window:
    ``last`` set with no ``first`` and no ``before`` bound (``before`` + ``last``
    resolves to a forward offset window the forward branch already handles). In
    that branch ``SliceMetadata`` sets ``end = sys.maxsize`` so ``expected is
    None``, and the row-count bound is the literal ``last`` (the reversed
    ``__lte`` row filter) - passing ``expected`` would never apply the bound and
    the window would over-fetch every child row.

    An ``after``-bearing backward window (``after`` + ``last``, no ``first`` / no
    ``before``) is NOT reversed: ``SliceMetadata`` resolves a non-zero offset
    (``start = int(after) + 1``), but the reversed row number partitions over the
    WHOLE parent partition, not the ``after``-filtered subset, so the forward
    ``_dst_row_number`` the resolver derives ``hasPreviousPage`` / cursors from
    would diverge from the per-parent pipeline whenever the after-remainder is
    ``<= last`` rows. ``SliceMetadata`` cannot express this shape as a clean
    forward window either (``end == sys.maxsize`` so ``expected is None``, an
    uncapped tail). Per spec-033 Decision 5 this falls back per-parent rather than
    approximating, so raise ``UnwindowableConnection`` to leave it unplanned.

    Strawberry's metadata is a Python slice, so only a nonnegative,
    non-inverted interval can be translated to positive SQL row numbers. An
    inverted ``after`` + ``before`` interval has a negative ``expected`` and
    means an empty Python slice, not an unbounded SQL tail, so it falls back per
    parent under spec-033 Decision 5. A correctly prefixed but forged negative
    cursor can produce a negative ``start`` or ``end``; classify that as malformed
    pagination (``TypeError``), not a valid fallback, so strictness cannot mask
    the field's own negative-index error.
    """
    slice_meta = SliceMetadata.from_arguments(
        info,
        before=before,
        after=after,
        first=first,
        last=last,
        max_results=max_results,
    )
    reverse = isinstance(last, int) and not isinstance(first, int) and before is None
    if slice_meta.start < 0:
        raise TypeError("Argument 'after' contains a non-existing value.")
    if slice_meta.end < 0:
        raise TypeError("Argument 'before' contains a non-existing value.")
    if reverse and after is not None:
        # Offset-bearing backward window: the reversed window's whole-partition
        # row numbering cannot honor the ``after`` offset (spec-033 Decision 5).
        raise UnwindowableConnection
    if slice_meta.expected is not None and slice_meta.expected < 0:
        # SQL row numbers cannot reproduce an inverted Python slice. Fall back
        # instead of approximating it as an unbounded forward tail.
        raise UnwindowableConnection
    limit = last if reverse else slice_meta.expected
    return ConnectionWindowBounds(slice_meta.start, limit, reverse)


#: Strawberry's ``StrawberryConfig.relay_max_results`` default, mirrored for
#: the keyset bounds derivation when neither an explicit ``max_results`` nor
#: a readable schema config is in reach (the same terminal default
#: ``SliceMetadata.from_arguments`` would land on through ``info``).
_RELAY_MAX_RESULTS_DEFAULT = 100


def resolve_relay_max_results(info: Any, max_results: int | None) -> int:
    """Resolve the effective ``relay_max_results`` cap for a keyset window.

    Precedence mirrors ``SliceMetadata.from_arguments``: an explicit
    ``max_results`` wins; otherwise the Strawberry schema config is read off
    ``info`` - accepting BOTH the resolve-time Strawberry ``Info`` shape
    (``info.schema.config``) and the plan-time graphql-core shape (config on
    ``info.schema._strawberry_schema``, the same brittle-private contract
    ``walker.py::_relay_max_results_from_info`` centralizes for the offset
    path) - and finally Strawberry's documented default. One resolver for
    both halves so the plan-time and resolve-time caps are the same number
    (the cursor-parity invariant's keyset leg).
    """
    if max_results is not None:
        return max_results
    schema = getattr(info, "schema", None)
    config = getattr(getattr(schema, "_strawberry_schema", None), "config", None)
    if config is None:
        config = getattr(schema, "config", None)
    cap = getattr(config, "relay_max_results", None)
    return cap if cap is not None else _RELAY_MAX_RESULTS_DEFAULT


def derive_keyset_window_bounds(
    info: Any,
    *,
    before: Any,
    after: Any,  # noqa: ARG001 - signature parity with the offset twin; the seek, not the bounds, consumes it.
    first: Any,
    last: Any,
    max_results: int | None,
) -> ConnectionWindowBounds:
    """Derive the window bounds for a KEYSET (``cursor_field``) connection.

    The keyset twin of ``derive_connection_window_bounds``: a keyset cursor
    is not an offset, so ``SliceMetadata`` cannot parse it - the bounds
    derivation forks BEFORE the offset engine and this helper owns the
    keyset fork for both halves (the plan-time walker and the resolve-time
    window consumer), so the two windows agree by construction. Cursor
    DECODING is deliberately not done here (``keyset.decode_keyset_cursor``
    owns it); this is pure slice arithmetic:

    - A keyset window is FORWARD-ONLY and always starts at offset 0 (the
      seek predicate, not a row offset, positions the page). ``limit`` is
      ``first`` when supplied (validated against the same negative /
      over-``max_results`` rules ``SliceMetadata`` applies, with its exact
      error text so the consumer-visible errors do not fork), else the
      effective ``relay_max_results`` cap - matching the root / per-parent
      keyset slicer.
    - Backward shapes (``last`` with no ``first``, or any ``before:``) raise
      ``UnwindowableConnection``: the reversed keyset window is not planned
      in v1, and the per-parent / root keyset slicer resolves those shapes
      correctly instead (the spec-033 Decision-5 fallback discipline).
    - ``first`` + ``last`` combined stays for the resolver's own
      mutual-exclusivity guard - here it is simply forward (``first`` wins
      the bound), matching the offset path's flow where the guard raises
      before any window is consumed.
    """
    if before is not None or (isinstance(last, int) and not isinstance(first, int)):
        raise UnwindowableConnection
    cap = resolve_relay_max_results(info, max_results)
    limit = cap
    if isinstance(first, int):
        if first < 0:
            raise ValueError("Argument 'first' must be a non-negative integer.")
        if first > cap:
            raise ValueError(f"Argument 'first' cannot be higher than {cap}.")
        limit = first
    return ConnectionWindowBounds(0, limit, False)
