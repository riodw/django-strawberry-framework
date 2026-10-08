"""Shared connection contracts for sidecars, fetch modes, offset cursors, windows, and page bounds.

A cycle-safe home for three correctness contracts that the optimizer planner
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
* The offset pagination validator (``validate_offset_pagination``, over
  ``decode_offset_cursor`` and ``assert_relay_pagination_bound``) - the one
  validator of an offset page's ``after`` / ``before`` cursors and ``first`` /
  ``last`` bounds, read by the window derivation above and by the resolver's
  non-window slicing tail, so the planned window and every
  ``ListConnection``-sliced source accept and reject the same arguments. Each
  rejection is a ``PaginationArgumentError`` raised where the argument is
  validated: the package's own validation constructs the client-facing error,
  so an exception from a consumer source or from row hydration is never caught
  and re-raised as one.
* The connection sidecar kwarg names and the presence predicates over them -
  the walker refuses to window-plan a sidecar-bearing nested connection, and
  the resolver refuses to consume a window when sidecar kwargs are present
  (spec-032 Decision 6). Those two decisions must always read the same kwarg
  family, which is why the extraction and both predicates live here rather
  than at either caller. A future sidecar (e.g. ``search``) is NOT a one-line
  edit: ``connection_sidecar_inputs_from_kwargs`` returns a NAMED pair and
  every caller destructures it, so a third member is a deliberate signature
  change that surfaces at each consumer instead of being silently absorbed.

This module depends on neither ``connection.py`` nor ``optimizer/walker.py`` so
both can import it without a cycle. Plan-time argument coercion (an inline Int
literal arrives as a token STRING; a Strawberry resolver argument is already
``int``) is deliberately NOT owned here - it is the nested planner's concern and
stays in ``optimizer/nested_planner.py::_coerce_pagination_int`` (the walker
re-exports the same helper for argument-comparison); this helper assumes its
``first`` / ``last`` are already the values ``SliceMetadata`` will gate on.
"""

from __future__ import annotations

import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Protocol, TypeVar, cast

import strawberry
from graphql import GraphQLError
from strawberry import relay
from strawberry.relay.utils import SliceMetadata, from_base64

from ..exceptions import DjangoStrawberryFrameworkError, OptimizerError
from ..resource_policy import effective_bound, policy_from_info
from .input_values import is_inactive_value
from .typing import schema_config_from_info

if TYPE_CHECKING:
    from strawberry import Info

    from .typing import EitherInfo

_FirstT = TypeVar("_FirstT")
_LastT = TypeVar("_LastT")
_RowT = TypeVar("_RowT")

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

#: The sentinel row an n+1 next-page probe overfetches, in BOTH pagination
#: domains: the window domain (a row-number ceiling or in-branch ``LIMIT``
#: raised by this much) and the value domain (``connection.py``'s keyset page,
#: which fetches ``page_size + this`` and truncates). The two derive their page
#: flags differently - row-number based vs ``len``-based - and that difference is
#: deliberate, but the SENTINEL COUNT is one fact, and it was a bare ``1``
#: in each domain under a docstring claiming the arithmetic had a single owner.
NEXT_PAGE_PROBE_ROWS = 1


# basedpyright: ``GraphQLError.__init__`` calls ``super().__init__(message)``, which reaches
# ``BaseException.__init__`` through the package base (it defines no ``__init__``)
class PaginationArgumentError(GraphQLError, DjangoStrawberryFrameworkError):  # pyright: ignore[reportUnsafeMultipleInheritance]
    """An offset cursor or a connection page size was invalid.

    Two rejections raise it: an offset ``after`` / ``before`` cursor that
    ``decode_offset_cursor`` does not accept, and a negative or over-cap
    ``first`` / ``last`` that ``assert_relay_pagination_bound`` refuses on an
    offset page, a keyset page or a planned window. A keyset (``Meta.cursor_field``)
    cursor is not one of them: its rejection is the keyset codec's own
    ``GraphQLError`` (``keyset.py::_invalid_cursor_error``), with its own wording.

    Dual-inherits ``GraphQLError`` (so the rejection travels the wire as the
    field's own error entry, which the production error policy treats as a
    deliberate client-facing statement) and ``DjangoStrawberryFrameworkError``
    (so consumers can catch it alongside any other framework error). The
    ``ListArgumentError`` precedent, without ``extensions``: the message is
    Strawberry's own ``SliceMetadata.from_arguments`` wording, byte for byte, so
    one invalid page size gets one message on every path.

    Raised only where the package validates an argument, never by catching an
    exception and re-raising its text: an exception from a consumer source or
    from row hydration is not a pagination statement, so the policy masks it.
    """


class UnwindowableConnection(Exception):  # noqa: N818 - control-flow signal, not a surfaced error
    """Internal signal: this pagination shape cannot be served by a windowed prefetch.

    Raised by ``derive_connection_window_bounds`` when Strawberry's Python-slice
    metadata cannot be represented by the SQL row-number window without changing
    results or page flags. This includes offset-bearing backward windows
    (``after`` + ``last``) and inverted ``after`` + ``before`` intervals. Per
    spec-033 Decision 5 these valid shapes fall back per parent rather than being
    approximated. An invalid pagination argument (``validate_offset_pagination``)
    raises ``PaginationArgumentError`` instead, keeping the field-local pagination
    error.

    A control-flow sentinel, deliberately NOT a ``DjangoStrawberryFrameworkError``
    and NOT a ``PaginationArgumentError``: the walker catches the pagination
    *errors* to leave a selection unplanned while
    still recording the field as accounted-for (it will raise its OWN error), but
    must treat THIS shape as a fully-unplanned Decision-6 fallback (no
    ``planned_resolver_keys`` entry) so the per-parent access stays visible to the
    strictness contract. A distinct type keeps the two paths separable.
    """


def connection_sidecar_inputs_from_kwargs(
    kwargs: Mapping[str, object] | None,
) -> tuple[object, object]:
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
    if not kwargs:
        return None, None
    order_by_input = kwargs.get(CONNECTION_ORDER_KWARG)
    if order_by_input is None:
        order_by_input = kwargs.get(CONNECTION_ORDER_KWARG_GRAPHQL)
    return kwargs.get(CONNECTION_FILTER_KWARG), order_by_input


def is_supplied(value: object) -> bool:
    """Return whether a connection argument was actually supplied by the client.

    The connection surfaces' spelling of the package's ONE active-input rule,
    ``utils/input_values.py::is_inactive_value``, whose docstring already
    claims to be that single rule. It was being re-typed as
    ``value is not None and value is not strawberry.UNSET`` at 15 sites across
    the two connection modules - the exact inverse, hand-written each time.

    The rule lives in ``input_values.py`` (which deliberately imports no
    strawberry, so the traversal primitives stay usable below the schema
    layer); only the ``UNSET`` sentinel binding lives here.
    """
    return not is_inactive_value(value, unset_sentinel=strawberry.UNSET)


def is_backward_shape(first: object, last: object) -> bool:
    """Return whether the pagination arguments describe a BACKWARD (``last``-only) page.

    The core Relay shape test: ``last`` was given as an ``int`` and ``first``
    was not. Three sites read it: the window derivation ANDs
    ``not before_supplied`` onto the core, the keyset resolver and the keyset
    bounds add nothing. That extra term is a real per-site difference and stays
    explicit at its call site; what is shared is only this core, so a change to
    the core is one edit and the variation between the sites stays visible.
    """
    return isinstance(last, int) and not isinstance(first, int)


def page_arguments(
    first: _FirstT,
    last: _LastT,
    *,
    cap: int,
) -> tuple[_FirstT | int, _LastT | None]:
    """Return the ``(first, last)`` every connection page is sliced with, offset and keyset alike.

    ``last: 0`` with no ``int`` ``first`` is the ``first: 0`` page (Strawberry would slice
    ``edges[-0:]``, the whole list). ``SliceMetadata`` applies its default page only when no
    ``before`` cursor set ``end``; with neither page argument an ``int``, the page is
    ``first = cap`` (graphene-django's rule), so every page is bounded by ``cap``.
    """
    if last == 0 and not isinstance(first, int):
        return 0, None
    if isinstance(first, int) or isinstance(last, int):
        return first, last
    return cap, last


def has_connection_sidecar_input(*, filter_input: object, order_by_input: object) -> bool:
    """Return whether either already-extracted sidecar input is present."""
    return is_supplied(filter_input) or is_supplied(order_by_input)


def has_connection_sidecar_kwargs(kwargs: Mapping[str, object] | None) -> bool:
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
    range AND for a parent with no children at all, which an unmarked window
    could only settle with a per-parent fallback. spec-033 Decision 5
    disambiguates these shapes with marker rows; reversed (``last``-only) windows never plan markers.

    The plan-time/resolve-time contract shared - like the sidecar-kwarg family
    above - by everything that must agree on "ambiguous": the window builders
    that ADD the marker rows (``utils/connections.py::window_range_plan``, feeding both
    ``apply_window_pagination`` and the lateral SQL) and the resolver that
    CONSUMES rows as marker-classified (``connection.py::_resolve_from_window``).
    The count decision is a SEPARATE axis owned by ``FetchMode`` /
    ``WindowRangePlan.fetch_mode`` - these ambiguous shapes are NOT
    shape-forced to a count: the offset page composes the count-free probe
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
    leaves the probe off, but that does not imply a count. Under the
    ``FetchMode`` policy a shape needs the ``COUNT(1) OVER`` only when it
    is ``COUNTED`` (``totalCount`` observed, or the ``first: 0`` marker shape) -
    an unbounded forward or reversed ``last``-only page is ``CONSTANT_FALSE``
    (``hasNextPage`` served as a constant ``False``, no count) and a bounded
    edges-only page is ``NONE`` (nothing count-derived is observable), both
    count-free. On the offset page the
    probe COMPOSES with ``add_marker_rows`` (the marker keeps each partition's
    row 1 while the sentinel answers ``hasNextPage``), so probe and markers are
    NOT mutually exclusive - but probe and count are (probe XOR
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
        """The sentinel-row count the probe adds to a fetch bound (the sentinel iff probing).

        The window domain's owner of the n+1 arithmetic: ``fetch_upper_bound``
        and ``fetch_limit`` both add THIS instead of each spelling their own
        ``+1``, so the two bounds cannot drift. Zero when the probe is off, so
        both bounds equal their page semantics by construction. The sentinel
        COUNT itself is ``NEXT_PAGE_PROBE_ROWS``, shared with the value domain's
        keyset page in ``connection.py`` - which always probes, so it adds the
        constant unconditionally rather than through this gate.
        """
        return NEXT_PAGE_PROBE_ROWS if self.next_page_probe else 0

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
        ``next_page_probe`` (``mode is FetchMode.PROBED``), so the two cannot
        be derived independently. Called by
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
    - A negative offset likewise raises ``OptimizerError``. An offset cursor never
      derives one (``decode_offset_cursor`` rejects a negative index upstream), but
      direct request objects must not turn one into an absolute SQL row-number floor.

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
    upper_bound = (limit if reverse else offset + limit) if limit is not None else None
    ambiguous = keyset_counted or is_ambiguous_empty_window(offset, limit, reverse=reverse)
    plain_first_page = not reverse and offset == 0 and limit is not None and limit > 0
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


class _RawWindowArguments(Protocol):
    """The raw window arguments a window-carrying dataclass exposes."""

    @property
    def offset(self) -> int: ...
    @property
    def limit(self) -> int | None: ...
    @property
    def reverse(self) -> bool: ...
    @property
    def next_page_probe(self) -> bool: ...
    @property
    def with_total_count(self) -> bool: ...


def assert_window_fetch_mode_for(window: _RawWindowArguments) -> None:
    """``assert_window_fetch_mode`` for callers holding RAW window arguments.

    ``NestedConnectionRequest`` and ``LateralWindowSpec`` carry
    ``(offset, limit, reverse, next_page_probe, with_total_count)`` rather than a
    resolved ``WindowRangePlan``; this reads those attributes, resolves the plan
    through the shared ``window_range_plan``, and delegates, so the
    effective-state rule is spelled exactly once. Both dataclasses pass
    ``self`` from ``__post_init__``.
    """
    assert_window_fetch_mode(
        window_range_plan(
            offset=window.offset,
            limit=window.limit,
            reverse=window.reverse,
            next_page_probe=window.next_page_probe,
        ),
        with_total_count=window.with_total_count,
    )


def split_window_rows(
    rows: Iterable[_RowT],
    range_plan: WindowRangePlan,
    *,
    row_number: str,
) -> tuple[list[_RowT], bool]:
    """Split annotated window ``rows`` into page rows and dropped sentinel rows.

    Returns ``(page_rows, probe_row_seen)``. The one home for sentinel-row
    exclusion, owning the sentinel shapes the window may carry. ``add_marker_rows``
    and ``next_page_probe`` are NOT mutually exclusive: they COMPOSE on the
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
    ``connection.py::_resolve_from_window`` are the resolve-side surface the
    keyset-cursor windows ride as well (a counted keyset seek numbers ``rn``
    page-relatively, planned through ``window_range_plan(keyset_counted=...)``) -
    everything else consumes ``(page_rows, probe_row_seen)`` unchanged.
    """
    row_list = list(rows) if not isinstance(rows, list) else rows
    if range_plan.add_marker_rows and range_plan.next_page_probe:
        # Composed offset page: the marker (rn == 1) and the probe sentinel
        # (rn == fetch_upper_bound == upper_bound + 1) are both dropped; the page
        # proper is the rows strictly past the offset and within the page ceiling.
        page_rows = [
            row
            for row in row_list
            if range_plan.offset < getattr(row, row_number) <= range_plan.upper_bound
        ]
        probe_row_seen = any(
            getattr(row, row_number) == range_plan.fetch_upper_bound for row in row_list
        )
        return page_rows, probe_row_seen
    if range_plan.add_marker_rows:
        if range_plan.limit == 0:
            return [], False
        return [row for row in row_list if getattr(row, row_number) > range_plan.offset], False
    if range_plan.next_page_probe and range_plan.upper_bound is not None:
        page_rows = [row for row in row_list if getattr(row, row_number) <= range_plan.upper_bound]
        return page_rows, len(page_rows) < len(row_list)
    return list(row_list), False


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


#: Digits in ``sys.maxsize``, the exclusive upper bound of an offset cursor index:
#: a longer payload is rejected before ``int()`` converts it.
_OFFSET_CURSOR_MAX_DIGITS = len(str(sys.maxsize))


def decode_offset_cursor(value: str | None, *, argument: str) -> int | None:
    """Decode one ``after`` / ``before`` offset cursor into the row index it names.

    The one validator of an offset cursor's position, read by both offset
    entries: the window derivation (``derive_connection_window_bounds``, at plan
    and resolve time) and the non-window slicing tail
    (``connection.py::_consume_fallback``) every other offset source reaches.
    Strawberry's ``SliceMetadata.from_arguments`` checks only the prefix and runs
    the payload through ``int()``, so a correctly prefixed negative index would
    reach Python slicing (which wraps), ``islice`` or Django's ``QuerySet``
    slicing (each with its own error text) as a position.

    Returns ``None`` when the cursor is absent by the engine's truthiness
    (``None``, ``""``, or a falsy sentinel such as ``UNSET``): ``SliceMetadata``
    reads ``if after:``, so an empty string sets no bound. Otherwise accepts only
    the form the package and ``ListConnection`` mint: ``relay.Edge.CURSOR_PREFIX``,
    a colon, and a canonical decimal (ASCII digits, no sign, no padding, no
    leading zero) in ``0 <= index < sys.maxsize``. Both mints are non-negative by
    construction (``ListConnection`` mints ``start + i``; the window mints the row
    number minus one), so a negative or non-canonical payload is never a cursor
    this API issued. The upper bound is the largest index a row can have: no
    Python sequence is longer than ``sys.maxsize``, ``SliceMetadata`` reserves
    ``sys.maxsize`` as its unbounded-end sentinel, and ``after`` adds one, so
    ``sys.maxsize - 1`` is the last index whose start still fits a 64-bit SQL
    ``OFFSET`` (an ordinary past-the-end page). The length is compared before
    ``int()`` runs, so an arbitrarily long digit string is never converted. Any
    other value raises ``PaginationArgumentError`` with Strawberry's own
    foreign-prefix wording, which the walker reads as malformed pagination and
    both resolve-time callers let surface as the field's own error.
    """
    if not value:
        return None
    rejection = PaginationArgumentError(f"Argument '{argument}' contains a non-existing value.")
    try:
        prefix, raw = from_base64(value)
    except ValueError:
        raise rejection from None
    if prefix != relay.Edge.CURSOR_PREFIX or not (raw.isascii() and raw.isdigit()):
        raise rejection
    if len(raw) > _OFFSET_CURSOR_MAX_DIGITS:
        raise rejection
    position = int(raw)
    if position >= sys.maxsize or str(position) != raw:
        raise rejection
    return position


def derive_connection_window_bounds(
    info: EitherInfo | None,
    *,
    before: str | None,
    after: str | None,
    first: int | None,
    last: int | None,
    max_results: int | None,
) -> ConnectionWindowBounds:
    """Derive the window ``(offset, limit, reverse)`` from pagination arguments.

    Owns the ``reverse`` predicate and the ``limit`` rule (the cursor-parity
    contract), running the arguments through Strawberry's
    ``SliceMetadata.from_arguments`` - the same engine both the plan-time walker
    and the resolve-time pipeline use. ``max_results`` is passed EXPLICITLY (the
    walker's graphql-core ``info.schema`` has no ``.config`` for the engine to
    read), and is narrowed through the request policy first, so plan-time and
    resolve-time caps include the same ``max_page_size`` ceiling. The arguments
    handed to the engine go through ``page_arguments``, so a ``before`` cursor
    with no page argument is bounded by that same cap and ``last: 0`` is the
    ``first: 0`` window.

    The arguments pass ``validate_offset_pagination`` before the engine sees
    them, so an invalid cursor or a negative / over-cap ``first`` / ``last``
    raises ``PaginationArgumentError`` with the engine's own wording and the
    engine itself never rejects. The walker catches it to leave the selection
    unplanned (Decision 4 step f); the resolver lets it surface as the field's
    own pagination error.

    Backward (``last``-only) pagination needs the reversed-row-number window:
    ``last`` set with no ``first`` and no ``before`` bound (``before`` + ``last``
    resolves to a forward offset window the forward branch already handles; an
    empty-string ``before`` is no bound, exactly as in the engine). In
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

    Both cursors go through ``decode_offset_cursor`` before the engine sees them,
    so a negative or non-canonical index raises ``PaginationArgumentError``
    (malformed pagination) and ``start`` / ``end`` are never negative. Strawberry's metadata
    is a Python slice, so only a non-inverted interval can be translated to SQL
    row numbers. An inverted ``after`` + ``before`` interval has a negative
    ``expected`` and means an empty Python slice, not an unbounded SQL tail, so it
    falls back per parent under spec-033 Decision 5.
    """
    effective_max_results = resolve_relay_max_results(info, max_results)
    first, last = page_arguments(first, last, cap=effective_max_results)
    validate_offset_pagination(
        before=before,
        after=after,
        first=first,
        last=last,
        cap=effective_max_results,
    )
    slice_meta = SliceMetadata.from_arguments(
        # The engine reads ``info`` only to find a cap when ``max_results`` is
        # ``None``, and ``effective_max_results`` is always an ``int``.
        cast("Info[object, object]", info),
        before=before,
        after=after,
        first=first,
        last=last,
        max_results=effective_max_results,
    )
    # Cursor presence is the engine's truthiness, deliberately NOT the
    # package's ``is_supplied`` rule (under which ``""`` is active):
    # ``SliceMetadata.from_arguments`` reads ``if before:`` / ``if after:``, so
    # an empty-string cursor is absent from the slice it builds. Reading it as
    # present here would plan ``last: N, before: ""`` as a forward window while
    # the engine serves the backward tail.
    before_supplied = bool(before)
    after_supplied = bool(after)
    reverse = is_backward_shape(first, last) and not before_supplied
    if reverse and after_supplied:
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


def assert_relay_pagination_bound(argument: str, value: object, *, cap: int) -> None:
    """Raise ``SliceMetadata``'s ``PaginationArgumentError`` for a negative or over-cap page size.

    The ONE spelling of the Relay ``first`` / ``last`` bound check, on both
    forks. The keyset fork cannot run ``SliceMetadata.from_arguments`` (a keyset
    cursor is not an offset), so ``derive_keyset_window_bounds`` (plan/resolve
    window bounds) and the root / per-parent keyset slicer
    (``connection.py::_resolve_keyset_connection``) call it directly; the offset
    fork reaches it through ``validate_offset_pagination``. A connection's
    consumer-visible pagination errors therefore cannot fork between the two
    vocabularies or between the windowed and per-parent paths. Non-``int``
    values are ignored - matching ``SliceMetadata``'s ``isinstance(..., int)``
    gate that skips the bound.
    """
    if not isinstance(value, int):
        return
    if value < 0:
        raise PaginationArgumentError(f"Argument '{argument}' must be a non-negative integer.")
    if value > cap:
        raise PaginationArgumentError(f"Argument '{argument}' cannot be higher than {cap}.")


def validate_offset_pagination(
    *,
    before: str | None,
    after: str | None,
    first: object,
    last: object,
    cap: int,
) -> None:
    """Reject every invalid offset pagination argument ``SliceMetadata.from_arguments`` rejects.

    The package's own validation of an offset page, run before anything slices,
    in the engine's check order: ``after``, ``before``, ``first``, ``last``, each
    with the engine's exact message, so the first invalid argument a client
    sends names the same argument with the same text it always did. The
    cursors go through ``decode_offset_cursor`` (which is also strictly
    narrower than the engine: a negative or non-canonical index is refused,
    never sliced) and the bounds through ``assert_relay_pagination_bound``
    against ``cap``, the already-resolved ``max_results`` the engine will be
    handed. ``first`` and ``last`` are each checked when supplied, as the
    engine checks them; their mutual exclusivity is the resolver's own guard.

    Once this returns, the engine raises nothing for these arguments, so the
    one window derivation (``derive_connection_window_bounds``) and the one
    non-window slicing tail (``connection.py::_consume_fallback``) can call the
    engine and ``ListConnection`` without a ``try``: anything they still raise
    comes from the source or the rows, not from the client's arguments.
    """
    decode_offset_cursor(after, argument="after")
    decode_offset_cursor(before, argument="before")
    assert_relay_pagination_bound("first", first, cap=cap)
    assert_relay_pagination_bound("last", last, cap=cap)


def relay_max_results_from_info(info: EitherInfo | None) -> int | None:
    """Read the configured ``relay_max_results``, or ``None`` when none is reachable.

    THE config dig, for both sides of the cursor-parity invariant's keyset leg.
    ``schema_config_from_info`` handles the two ``info`` shapes: the resolve-time
    Strawberry ``Info`` that ``SliceMetadata.from_arguments`` expects, and the
    plan-time raw graphql-core ``GraphQLResolveInfo`` whose ``.schema`` is a bare
    ``GraphQLSchema`` with no ``.config`` (the optimizer walker's middleware
    layer). Neither caller dereferences ``info.schema.config`` itself.

    Returning ``None`` rather than a default is deliberate and is the whole
    difference from :func:`resolve_relay_max_results`: the planner needs "no
    cap configured" to stay distinguishable so the engine default applies
    downstream, while the resolver must land on a concrete number.
    """
    return getattr(schema_config_from_info(info), "relay_max_results", None)


def resolve_relay_max_results(info: EitherInfo | None, max_results: int | None) -> int:
    """Resolve the effective ``relay_max_results`` cap for a keyset window.

    Precedence mirrors ``SliceMetadata.from_arguments``: an explicit
    ``max_results`` wins; otherwise :func:`relay_max_results_from_info` reads the
    schema config, and finally Strawberry's documented default applies. The dig
    itself is shared with the planner so the plan-time and resolve-time caps
    cannot read different attribute paths.
    """
    if is_supplied(max_results):
        cap = max_results
    else:
        configured = relay_max_results_from_info(info)
        cap = configured if is_supplied(configured) else _RELAY_MAX_RESULTS_DEFAULT
    # The request policy is a CEILING over whichever cap won above, never a
    # replacement for it: a connection can be narrower than the policy and can
    # never be wider (``resource_policy.py::effective_bound``). This is the seam
    # both the plan-time walker and the resolve-time window read, so clamping
    # here keeps the two windows in agreement by construction.
    return effective_bound(policy_from_info(info).max_page_size, cap)


def derive_keyset_window_bounds(
    info: EitherInfo | None,
    *,
    before: object,
    after: object,  # noqa: ARG001 - signature parity with the offset twin; the seek, not the bounds, consumes it.
    first: int | None,
    last: object,
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
      ``first`` when supplied (validated via ``assert_relay_pagination_bound``
      against the same negative / over-``max_results`` rules ``SliceMetadata``
      applies, with its exact error text so the consumer-visible errors do not
      fork), else the effective ``relay_max_results`` cap - matching the root /
      per-parent keyset slicer.
    - The arguments go through ``page_arguments`` first, as on the offset
      fork, so ``last: 0`` is the forward ``first: 0`` window. Backward shapes
      (``last`` with no ``first``, or any ``before:``) raise
      ``UnwindowableConnection``: the reversed keyset window is not planned
      in v1, and the per-parent / root keyset slicer resolves those shapes
      correctly instead (the spec-033 Decision-5 fallback discipline).
    - ``first`` + ``last`` combined stays for the resolver's own
      mutual-exclusivity guard - here it is simply forward (``first`` wins
      the bound), matching the offset path's flow where the guard raises
      before any window is consumed.
    """
    cap = resolve_relay_max_results(info, max_results)
    first, last = page_arguments(first, last, cap=cap)
    if is_supplied(before) or is_backward_shape(first, last):
        raise UnwindowableConnection
    assert_relay_pagination_bound("first", first, cap=cap)
    return ConnectionWindowBounds(0, first, False)
