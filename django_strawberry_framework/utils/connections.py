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

# The Python kwarg names for the connection sidecar arguments. Strawberry
# exposes ``order_by`` as the camelCase ``orderBy`` GraphQL argument; this is the
# PYTHON kwarg name (the key in the resolver ``**kwargs`` and in the walker's
# converted ``sel.arguments``), kept distinct from the display string on purpose.
CONNECTION_FILTER_KWARG = "filter"
CONNECTION_ORDER_KWARG = "order_by"
CONNECTION_SIDECAR_KWARGS = (CONNECTION_FILTER_KWARG, CONNECTION_ORDER_KWARG)


class UnwindowableConnection(Exception):  # noqa: N818 - control-flow signal, not a surfaced error
    """Internal signal: this pagination shape cannot be served by a windowed prefetch.

    Raised by ``derive_connection_window_bounds`` for an offset-bearing backward
    window (``after`` + ``last``, no ``first``, no ``before``). The reversed
    row-number window numbers rows from the partition END, so the forward
    ``_dst_row_number`` the resolver reads its page flags from spans the WHOLE
    partition, not the ``after``-filtered subset; pairing that with a non-zero
    ``after`` offset makes ``hasPreviousPage`` (and the offset cursor) diverge
    from the per-parent pipeline whenever the after-remainder is ``<= last`` rows
    (spec-033 Decision 5 scopes the reversed window to ``last``-only and defers
    the offset-bearing shapes to the per-parent fallback - "combinations the
    offset arithmetic cannot push down fall back per-parent rather than
    approximating").

    A control-flow sentinel, deliberately NOT a ``DjangoStrawberryFrameworkError``
    and NOT a ``ValueError`` / ``TypeError``: the walker catches the pagination
    *errors* (``ValueError`` / ``TypeError``) to leave a selection unplanned while
    still recording the field as accounted-for (it will raise its OWN error), but
    must treat THIS shape as a fully-unplanned Decision-6 fallback (no
    ``planned_resolver_keys`` entry) so the per-parent access stays visible to the
    Slice-4 strictness contract. A distinct type keeps the two paths separable.
    """


def connection_sidecar_inputs_from_kwargs(kwargs: dict[str, Any]) -> tuple[Any, Any]:
    """Extract ``(filter_input, order_by_input)`` from a resolver ``**kwargs`` dict.

    The single reader of the sidecar kwarg keys so the resolver bodies never
    re-spell ``kwargs.get("filter")`` / ``kwargs.get("order_by")``.
    """
    return kwargs.get(CONNECTION_FILTER_KWARG), kwargs.get(CONNECTION_ORDER_KWARG)


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
    ``add_marker_rows`` are mutually exclusive by construction. The ``+1`` lives
    in exactly one place - the ``fetch_upper_bound`` / ``fetch_limit`` derived
    bounds the renderers read UNCONDITIONALLY; ``upper_bound`` / ``limit`` keep
    their PAGE semantics (the resolver's split and the marker predicate depend
    on that). The plan-time decision is ``wants_next_page_probe``, the pure
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
    def fetch_upper_bound(self) -> int | None:
        """The inclusive row-number ceiling to FETCH (page bound plus the probe sentinel).

        Equals ``upper_bound`` whenever the probe is off, so every existing
        renderer call site and test is untouched by construction; adds the one
        sentinel row for the probe shape. The ``+1`` exists here and in
        ``fetch_limit`` only - the renderers never re-derive it.
        """
        if self.next_page_probe and self.upper_bound is not None:
            return self.upper_bound + 1
        return self.upper_bound

    @property
    def fetch_limit(self) -> int | None:
        """The plain-first-page in-branch ``LIMIT`` to FETCH (page size plus the probe sentinel).

        The lateral fast branch reads this instead of ``limit``; equal to
        ``limit`` when the probe is off.
        """
        if self.next_page_probe and self.limit is not None:
            return self.limit + 1
        return self.limit

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
) -> WindowRangePlan:
    """Resolve one slice window into its shared ``WindowRangePlan``.

    Pure and renderer-agnostic. Owns the two sentinel rules spelled once for
    every consumer:

    - ``limit is None`` OR Relay's ``sys.maxsize`` means "no upper bound"
      (the offset floor still applies). Normalized here so no renderer ever
      sees ``sys.maxsize``.
    - A negative limit is not a valid window and is treated as unbounded
      (unreachable through ``SliceMetadata`` - it raises on negative
      ``first`` / ``last`` - but direct callers get one deliberate rule
      instead of per-renderer drift).

    ``next_page_probe`` (the count-free ``hasNextPage`` overfetch) is honored
    only on the ``plain_first_page`` shape and ignored everywhere else, so a
    caller may pass the raw decision through without re-checking the shape and
    the ``add_marker_rows`` / ``next_page_probe`` fields stay mutually
    exclusive by construction.
    """
    if limit == sys.maxsize:
        limit = None
    lower_bound = offset if offset else None
    bounded = limit is not None and limit >= 0
    upper_bound = (limit if reverse else offset + limit) if bounded else None
    ambiguous = is_ambiguous_empty_window(offset, limit, reverse=reverse)
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
        next_page_probe=next_page_probe and plain_first_page,
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
    if reverse and after is not None:
        # Offset-bearing backward window: the reversed window's whole-partition
        # row numbering cannot honor the ``after`` offset (spec-033 Decision 5).
        raise UnwindowableConnection
    limit = last if reverse else slice_meta.expected
    return ConnectionWindowBounds(slice_meta.start, limit, reverse)
