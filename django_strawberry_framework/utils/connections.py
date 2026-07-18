"""Shared connection contracts for sidecars, fetch modes, offset/keyset windows, and pagination bounds.

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
from enum import Enum
from typing import Any

from strawberry.relay.utils import SliceMetadata

from ..exceptions import OptimizerError
from .typing import schema_config_from_info

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


class FetchMode(Enum):
    """The single fetch policy one window shape + its selection observers imply.

    The ONE source of truth for the count/probe decision, so the policy cannot
    drift between the planner
    (``optimizer/nested_planner.py::plan_connection_relation``, which derives
    ``with_total_count`` / ``next_page_probe`` from the mode) and the resolver
    (``connection.py::_resolve_from_window``, which reads the mode's shared shape
    predicates - ``probe_shape`` / ``constant_false_shape`` - off the returned
    rows' physical shape). Four disjoint modes, computed by
    ``WindowRangePlan.fetch_mode`` from ``(shape, total_selected,
    has_next_selected)``:

    * ``COUNTED`` - annotate the per-partition ``Count(1) OVER (PARTITION BY)``.
      Fires when ``totalCount`` is observed OR on the ``first: 0`` shape
      (``limit == 0``), whose marker IS a would-be sentinel (folding it into a
      probe is a later refinement). Maps to ``with_total_count=True``.
    * ``PROBED`` - serve ``hasNextPage`` from the count-free n+1 overfetch on a
      probe-eligible shape (plain ``first: N`` OR the bounded forward offset
      page) when ``hasNextPage`` is observed but ``totalCount`` is not. Maps to
      ``next_page_probe=True``.
    * ``CONSTANT_FALSE`` - serve ``hasNextPage`` as a constant ``False`` with no
      count and no probe: an unbounded forward page ends at the partition tail
      and a reversed ``last``-only page IS the tail.
    * ``NONE`` - no count-derived field is observable (an edges-only bounded
      forward page): neither a count nor a probe is needed.

    ``COUNTED`` and ``PROBED`` are mutually exclusive (probe XOR count, the
    invariant ``assert_window_fetch_mode`` enforces). ``CONSTANT_FALSE`` and
    ``NONE`` both leave the window count-free with no probe - they yield the same
    ``(with_total_count, next_page_probe)`` planner triple and differ only in the
    resolve-time ``hasNextPage`` derivation (served ``False`` vs never read).
    """

    COUNTED = "counted"
    PROBED = "probed"
    CONSTANT_FALSE = "constant_false"
    NONE = "none"


def _is_probe_shape(
    *,
    offset: int,
    limit: int | None,
    reverse: bool,
    plain_first_page: bool,
) -> bool:
    """Whether a window SHAPE can answer ``hasNextPage`` from an n+1 probe.

    The single spelling of the probe-shape predicate - the plain ``first: N``
    page (``plain_first_page``) OR the bounded forward offset page (``offset > 0``
    with a positive ``limit``). Shared by ``window_range_plan`` (deciding whether
    to honor a ``next_page_probe`` request) and ``WindowRangePlan.probe_shape``
    (which the resolver and ``fetch_mode`` read), so the three cannot drift.
    """
    return plain_first_page or (not reverse and offset > 0 and limit is not None and limit > 0)


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
    ``apply_window_pagination`` and the lateral SQL) and the resolver that
    CONSUMES rows as marker-classified (``connection.py::_resolve_from_window``).
    The count decision is a SEPARATE axis owned by ``FetchMode`` /
    ``WindowRangePlan.fetch_mode`` - these ambiguous shapes are NO LONGER
    shape-forced to a count (WS-A): the offset page composes the count-free probe
    with its marker, and only the ``first: 0`` marker still serves a count. One
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
    ``ORDER BY``/``LIMIT``. The count-vs-probe policy is NOT a stored field: it
    is derived on demand from ``fetch_mode`` (the single ``FetchMode`` source of
    truth), whose ``COUNTED`` / ``PROBED`` values the planner maps to
    ``with_total_count`` / ``next_page_probe`` and whose shape predicates
    (``probe_shape`` / ``constant_false_shape``) the resolver reads off the rows.

    ``next_page_probe`` marks the count-free ``hasNextPage`` overfetch (the
    n+1 probe): a window that fetches ONE sentinel row past the page so
    ``hasNextPage`` is answered by the sentinel's presence instead of a
    ``COUNT(1) OVER (PARTITION BY ...)`` that scans the whole partition. It is
    honored on the ``plain_first_page`` shape AND on the bounded forward
    offset page (``offset > 0`` with a positive ``limit``); every OTHER shape
    leaves the probe off, but that no longer implies a count. Under the WS-A
    fetch policy (``FetchMode``) a shape needs the ``COUNT(1) OVER`` only when it
    is ``COUNTED`` (``totalCount`` observed, or the ``first: 0`` marker shape) -
    an unbounded forward or reversed ``last``-only page is ``CONSTANT_FALSE``
    (``hasNextPage`` served as a constant ``False``, no count) and a bounded
    edges-only page is ``NONE`` (nothing count-derived is observable), both
    count-free. On the offset page the
    probe COMPOSES with ``add_marker_rows`` (the marker keeps each partition's
    row 1 while the sentinel answers ``hasNextPage``), so probe and markers are
    NO LONGER mutually exclusive - but probe and count still are (probe XOR
    count is the standing invariant, enforced by ``assert_window_fetch_mode``).
    The ``+1``
    sentinel arithmetic lives in exactly one place - the ``_probe_increment``
    primitive that both ``fetch_upper_bound`` and ``fetch_limit`` add to the
    derived bounds the renderers read UNCONDITIONALLY; ``upper_bound`` /
    ``limit`` keep their PAGE semantics (the resolver's split and the marker
    predicate depend on that). The plan-time decision is ``fetch_mode`` (whose
    ``PROBED`` value the planner maps to ``next_page_probe``); the resolver does
    NOT re-derive it from the selection (same-argument aliases share one window
    whose shape was fixed from the MERGED selection, so a per-alias re-derivation
    would drift) - it reads the probe off the window's physical shape instead
    (``connection.py::_resolve_from_window``, via the shared ``probe_shape``).
    """

    offset: int
    limit: int | None
    reverse: bool
    lower_bound: int | None
    upper_bound: int | None
    add_marker_rows: bool
    plain_first_page: bool
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

    @property
    def probe_shape(self) -> bool:
        """Whether this window's SHAPE can answer ``hasNextPage`` from an n+1 probe.

        True for the plain ``first: N`` page (``plain_first_page``) AND the
        bounded forward offset page (``offset > 0`` with a positive ``limit``) -
        the shapes whose ``hasNextPage`` a single overfetched sentinel row
        settles. Observer-free (the SHAPE half of ``FetchMode.PROBED``); the
        selection observers are layered on in ``fetch_mode``. The resolver reads
        this predicate off the window's physical shape to decide whether a
        count-absent window was overfetched, so the plan-time and resolve-time
        views of "is this a probe shape" cannot drift (both go through the shared
        ``_is_probe_shape``).
        """
        return _is_probe_shape(
            offset=self.offset,
            limit=self.limit,
            reverse=self.reverse,
            plain_first_page=self.plain_first_page,
        )

    @property
    def constant_false_shape(self) -> bool:
        """Whether this window's SHAPE serves ``hasNextPage`` as a constant ``False``.

        True for the unbounded forward page (no ``first`` -> the served page ends
        at the partition's last row) and the reversed ``last``-only page (which
        IS the tail). The SHAPE half of ``FetchMode.CONSTANT_FALSE``; both
        ``fetch_mode`` and the resolver's count-absent ``hasNextPage`` drift-guard
        exemption read it here. ``first: 0`` (``limit == 0``) is NOT constant-false
        - it is counted - and a keyset-counted marker shape carries its count, so
        both are excluded where this is consumed (``fetch_mode`` checks it only
        after ``COUNTED``; the resolver gates it on ``total is None``).
        """
        return self.limit is None or self.reverse

    def fetch_mode(self, *, has_next_selected: bool, total_selected: bool) -> FetchMode:
        """Resolve the ONE ``FetchMode`` this window + selection observers imply.

        The single source of truth the planner consumes for BOTH
        ``with_total_count`` (``mode is FetchMode.COUNTED``) and
        ``next_page_probe`` (``mode is FetchMode.PROBED``), replacing the two
        formerly-independent derivations. Called by
        ``optimizer/nested_planner.py::plan_connection_relation`` with the
        ``totalCount`` / ``hasNextPage`` observers from the merged selection
        (``optimizer/selections.py``). The resolver deliberately does NOT call
        this: same-argument aliases share one window planned from the MERGED
        selection, so re-deriving the mode per alias from each response key's
        ``info`` would drift - it reads the mode's shared shape predicates
        (``probe_shape`` / ``constant_false_shape``) off the window's physical
        shape instead (``connection.py::_resolve_from_window``).

        Order matters: ``COUNTED`` wins first (``totalCount`` observed, or the
        ``first: 0`` marker shape), so a ``probe_shape`` window with an observable
        ``totalCount`` is counted, never probed - keeping ``PROBED`` and
        ``COUNTED`` mutually exclusive (probe XOR count).
        """
        if total_selected or self.limit == 0:
            return FetchMode.COUNTED
        if self.probe_shape and has_next_selected:
            return FetchMode.PROBED
        if self.constant_false_shape:
            return FetchMode.CONSTANT_FALSE
        return FetchMode.NONE


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
    on the ``plain_first_page`` shape AND the bounded forward offset page
    (``offset > 0`` with a positive ``limit``), and ignored everywhere else, so
    a caller may pass the raw decision through without re-checking the shape. On
    the offset page the probe COMPOSES with ``add_marker_rows`` (both fields set
    at once); probe and count stay mutually exclusive by construction (probe XOR
    count).

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
    probe_shape = _is_probe_shape(
        offset=offset,
        limit=limit,
        reverse=reverse,
        plain_first_page=plain_first_page,
    )
    return WindowRangePlan(
        offset=offset,
        limit=limit,
        reverse=reverse,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        add_marker_rows=ambiguous and (lower_bound is not None or upper_bound is not None),
        plain_first_page=plain_first_page,
        next_page_probe=next_page_probe and probe_shape and not keyset_counted,
    )


def assert_window_fetch_mode(range_plan: WindowRangePlan, *, with_total_count: bool) -> None:
    """Enforce the probe/count mutual-exclusion contract on a RESOLVED window plan.

    The count-free ``hasNextPage`` probe (``range_plan.next_page_probe``, already
    normalized by ``window_range_plan`` to the ``plain_first_page`` OR bounded
    forward offset-page shape) fetches one sentinel row past the page and answers
    ``hasNextPage`` from its presence. A window that engages the probe must NOT
    also annotate the partition count: the resolver infers "no probe" from a
    present ``_dst_total_count`` and would pass the n+1 sentinel through as a real
    edge (``connection.py::_resolve_from_window``). The invariant is the
    EFFECTIVE state, not the raw flags - a ``next_page_probe`` request off a
    probe-eligible shape is inert (``window_range_plan`` drops it), so it may
    coexist with the count harmlessly and is not rejected here. Probe and
    ``add_marker_rows`` DO compose on the offset page (probe XOR count is the
    only exclusion this enforces).

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
    exclusion, owning the sentinel shapes the window may carry. ``add_marker_rows``
    and ``next_page_probe`` are NO LONGER mutually exclusive: they COMPOSE on the
    bounded forward offset page (marker keeps row 1, probe adds the sentinel past
    the page), so the composed case is handled FIRST:

    - ``add_marker_rows`` and ``next_page_probe`` (the composed offset page): the
      page proper is ``offset < rn <= upper_bound``; the marker (``rn == 1``) and
      the probe sentinel (``rn == fetch_upper_bound``) are both excluded from it.
      ``probe_row_seen`` reports whether the sentinel was present, which IS
      ``hasNextPage``.
    - ``add_marker_rows`` alone (the ambiguous ``after:`` / ``first: 0`` /
      unbounded offset shapes): each partition's row 1 is kept as a marker so an
      empty page and a childless parent stay distinguishable. The page proper is
      the rows past the offset (``limit == 0`` has no page at all);
      ``probe_row_seen`` is ``False`` (markers do not signal a next page).
    - ``next_page_probe`` alone (the count-free plain-first-page overfetch): the
      window fetched one row past the page (``rn == upper_bound + 1``). The page
      is the rows up to ``upper_bound``; ``probe_row_seen`` reports whether the
      sentinel was present, which IS ``hasNextPage`` - no ``_dst_total_count``
      needed.

    Render-agnostic: works identically for the ORM window and the lateral SQL
    because both keep FORWARD row numbers and the lateral fast branch computes
    ``rn`` BEFORE its ``LIMIT`` applies, so the sentinel is always the
    ``rn == upper_bound + 1`` row regardless of which renderer produced it.
    This helper plus the ``hasNextPage`` derivation in
    ``connection.py::_resolve_from_window`` are the resolve-side surface a
    future keyset-cursor backend (which makes ``rn`` page-relative) has to
    touch - everything else consumes ``(page_rows, probe_row_seen)`` unchanged.
    """
    if range_plan.add_marker_rows and range_plan.next_page_probe:
        # Composed offset page: the marker (rn == 1) and the probe sentinel
        # (rn == fetch_upper_bound == upper_bound + 1) are both dropped; the page
        # proper is the rows strictly past the offset and within the page ceiling.
        page_rows = [
            row
            for row in rows
            if range_plan.offset < getattr(row, row_number) <= range_plan.upper_bound
        ]
        probe_row_seen = any(
            getattr(row, row_number) == range_plan.fetch_upper_bound for row in rows
        )
        return page_rows, probe_row_seen
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
    ``max_results`` wins; otherwise the Strawberry schema config is read via
    ``schema_config_from_info`` (BOTH the resolve-time Strawberry ``Info``
    shape and the plan-time graphql-core ``_strawberry_schema`` shape) and
    finally Strawberry's documented default. One config dig shared with the
    planner's ``_relay_max_results_from_info`` (which returns ``None`` instead
    of this terminal default) so the plan-time and resolve-time caps read the
    same attribute path (the cursor-parity invariant's keyset leg).
    """
    if max_results is not None:
        return max_results
    cap = getattr(schema_config_from_info(info), "relay_max_results", None)
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
