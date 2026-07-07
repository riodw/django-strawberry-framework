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
