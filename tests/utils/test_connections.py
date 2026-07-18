"""Unit tests for the shared connection planner/resolver contracts.

Covers ``django_strawberry_framework/utils/connections.py`` -- the cycle-safe
home for the slice-window derivation and the sidecar-kwarg family that the
optimizer walker (plan time) and the Relay resolver (resolve time) must spell
identically.
"""

from types import SimpleNamespace

import pytest
from strawberry.relay.types import to_base64
from strawberry.relay.utils import SliceMetadata

from django_strawberry_framework.exceptions import OptimizerError
from django_strawberry_framework.utils.connections import (
    CONNECTION_FILTER_KWARG,
    CONNECTION_ORDER_KWARG,
    CONNECTION_SIDECAR_KWARGS,
    ConnectionWindowBounds,
    FetchMode,
    UnwindowableConnection,
    assert_window_fetch_mode,
    assert_window_fetch_mode_for,
    connection_sidecar_inputs_from_kwargs,
    derive_connection_window_bounds,
    has_connection_sidecar_input,
    has_connection_sidecar_kwargs,
    split_window_rows,
    window_range_plan,
)

# ``max_results`` is always passed explicitly below, so ``from_arguments`` never
# dereferences ``info`` (the ``info.schema.config.relay_max_results`` default is
# short-circuited) -- ``None`` is a safe stand-in for the engine ``Info`` here.
_MAX = 100


def test_last_only_window_limit_is_literal_last_not_expected():
    """A ``last``-only window's bound is the literal ``last``, NOT ``slice_meta.expected``.

    This is the load-bearing reverse-branch rule: ``SliceMetadata`` sets
    ``end = sys.maxsize`` for a ``last``-only window so ``expected is None``;
    passing ``expected`` as the bound would never apply the reversed ``__lte``
    row filter and the window would over-fetch every child row. The shared helper
    must return ``limit == last`` instead.
    """
    slice_meta = SliceMetadata.from_arguments(None, last=2, max_results=_MAX)
    assert slice_meta.expected is None  # the trap the helper must not fall into

    bounds = derive_connection_window_bounds(
        None,
        before=None,
        after=None,
        first=None,
        last=2,
        max_results=_MAX,
    )
    assert bounds == ConnectionWindowBounds(offset=0, limit=2, reverse=True)


def test_forward_window_limit_is_expected_and_not_reverse():
    """A forward ``first`` window is not reversed and bounds to ``expected``."""
    bounds = derive_connection_window_bounds(
        None,
        before=None,
        after=None,
        first=3,
        last=None,
        max_results=_MAX,
    )
    assert bounds == ConnectionWindowBounds(offset=0, limit=3, reverse=False)


def test_before_with_last_is_a_forward_window_not_reverse():
    """``before`` + ``last`` resolves to a forward offset window (reverse stays False)."""
    after = SliceMetadata.from_arguments(None, first=5, max_results=_MAX)
    # Build a real ``before`` cursor from the forward window's end so the helper
    # takes the ``before is not None`` path that keeps ``reverse`` False.
    from strawberry.relay.types import to_base64

    before_cursor = to_base64("arrayconnection", after.end)
    bounds = derive_connection_window_bounds(
        None,
        before=before_cursor,
        after=None,
        first=None,
        last=2,
        max_results=_MAX,
    )
    assert bounds.reverse is False


def test_after_with_last_is_unwindowable_not_reverse_with_offset():
    """``after`` + ``last`` raises ``UnwindowableConnection`` instead of a reverse window.

    The offset-bearing backward shape (no ``first`` / no ``before``) resolves a
    NON-ZERO offset through ``SliceMetadata`` (``start = int(after) + 1``), but
    the reversed row-number window partitions over the WHOLE parent partition, so
    the forward ``_dst_row_number`` the resolver reads its page flags from would
    diverge from the per-parent pipeline whenever the after-remainder is
    ``<= last`` rows. Pre-fix the helper returned ``reverse=True`` with that
    non-zero offset (the High); the fix makes it an unwindowable fallback so the
    walker leaves the selection unplanned and the per-parent pipeline serves it
    (spec-033 Decision 5).
    """
    after_cursor = to_base64("arrayconnection", "3")
    slice_meta = SliceMetadata.from_arguments(
        None,
        before=None,
        after=after_cursor,
        first=None,
        last=3,
        max_results=_MAX,
    )
    # The trap: a non-zero offset paired with the reversed-window shape.
    assert slice_meta.start == 4

    with pytest.raises(UnwindowableConnection):
        derive_connection_window_bounds(
            None,
            before=None,
            after=after_cursor,
            first=None,
            last=3,
            max_results=_MAX,
        )


def test_after_with_first_stays_a_windowed_forward_offset():
    """``after`` + ``first`` keeps a windowed forward offset window (not unwindowable).

    The companion to the ``after`` + ``last`` rejection: a forward offset window
    is fully expressible by ``SliceMetadata`` (``limit = expected``), so the fix
    must NOT reject it - only the backward (``last``) offset shape is unwindowable.
    """
    after_cursor = to_base64("arrayconnection", "2")
    bounds = derive_connection_window_bounds(
        None,
        before=None,
        after=after_cursor,
        first=2,
        last=None,
        max_results=_MAX,
    )
    assert bounds == ConnectionWindowBounds(offset=3, limit=2, reverse=False)


def test_inverted_after_before_is_unwindowable_not_a_negative_limit_window():
    """An inverted ``after`` + ``before`` window raises ``UnwindowableConnection``.

    When ``before`` resolves at or before ``after``, ``SliceMetadata`` yields
    ``start > end`` so ``expected`` is NEGATIVE (the range is empty). Pre-fix the
    helper passed that negative ``expected`` straight through as ``limit``, and
    the pre-fix ``window_range_plan`` read it as "no upper bound". The windowed
    prefetch therefore served the forward tail instead of the empty page from the
    per-parent ``ListConnection``. The fix makes it an unwindowable fallback
    (spec-033 Decision 5).
    """
    after_cursor = to_base64("arrayconnection", "3")
    before_cursor = to_base64("arrayconnection", "2")
    slice_meta = SliceMetadata.from_arguments(
        None,
        before=before_cursor,
        after=after_cursor,
        max_results=_MAX,
    )
    # The trap: a NEGATIVE expected (start 4 > end 2), which the pre-fix path
    # forwarded as a negative ``limit`` that the pre-fix range planner unbounded.
    assert slice_meta.start == 4
    assert slice_meta.expected == -2

    with pytest.raises(UnwindowableConnection):
        derive_connection_window_bounds(
            None,
            before=before_cursor,
            after=after_cursor,
            first=None,
            last=None,
            max_results=_MAX,
        )
    # The same inverted range with a trailing ``last:`` bound is unwindowable too.
    with pytest.raises(UnwindowableConnection):
        derive_connection_window_bounds(
            None,
            before=before_cursor,
            after=after_cursor,
            first=None,
            last=2,
            max_results=_MAX,
        )


def test_negative_after_cursor_start_is_malformed_not_windowable():
    """A forged negative offset stays a field-local pagination error."""
    after_cursor = to_base64("arrayconnection", "-2")
    slice_meta = SliceMetadata.from_arguments(
        None,
        after=after_cursor,
        first=2,
        max_results=_MAX,
    )
    assert slice_meta.start == -1
    assert slice_meta.expected == 2

    with pytest.raises(TypeError, match="Argument 'after' contains a non-existing value"):
        derive_connection_window_bounds(
            None,
            before=None,
            after=after_cursor,
            first=2,
            last=None,
            max_results=_MAX,
        )


def test_negative_before_cursor_end_is_malformed_not_inverted():
    """A forged negative end is malformed, not a strictness-visible fallback."""
    before_cursor = to_base64("arrayconnection", "-2")
    slice_meta = SliceMetadata.from_arguments(
        None,
        before=before_cursor,
        max_results=_MAX,
    )
    assert slice_meta.start == 0
    assert slice_meta.end == -2

    with pytest.raises(TypeError, match="Argument 'before' contains a non-existing value"):
        derive_connection_window_bounds(
            None,
            before=before_cursor,
            after=None,
            first=None,
            last=None,
            max_results=_MAX,
        )


def test_non_inverted_after_before_stays_a_windowed_forward_offset():
    """A NON-inverted ``after`` + ``before`` window stays windowable (guards over-rejection).

    ``after`` index 1, ``before`` index 4 resolves ``start=2``, ``end=4`` (a
    positive ``expected`` of 2), so the forward offset window is fully
    expressible - only the negative-``expected`` inverted shape is unwindowable.
    """
    bounds = derive_connection_window_bounds(
        None,
        before=to_base64("arrayconnection", "4"),
        after=to_base64("arrayconnection", "1"),
        first=None,
        last=None,
        max_results=_MAX,
    )
    assert bounds == ConnectionWindowBounds(offset=2, limit=2, reverse=False)


def test_zero_width_after_before_stays_windowable():
    """A zero-width interval is representable and must not be over-rejected."""
    bounds = derive_connection_window_bounds(
        None,
        before=to_base64("arrayconnection", "4"),
        after=to_base64("arrayconnection", "3"),
        first=None,
        last=None,
        max_results=_MAX,
    )
    assert bounds == ConnectionWindowBounds(offset=4, limit=0, reverse=False)


@pytest.mark.parametrize(
    ("offset", "limit", "message"),
    [(-1, 2, "window offset cannot be negative"), (4, -2, "window limit cannot be negative")],
)
def test_window_range_plan_rejects_negative_direct_bounds(offset, limit, message):
    """A malformed internal request fails loud instead of changing its range."""
    with pytest.raises(OptimizerError, match=message):
        window_range_plan(offset=offset, limit=limit, reverse=False)


def test_sidecar_kwarg_family_constants():
    """The sidecar kwarg family is the Python kwarg names ``filter`` / ``order_by``."""
    assert CONNECTION_FILTER_KWARG == "filter"
    assert CONNECTION_ORDER_KWARG == "order_by"
    assert CONNECTION_SIDECAR_KWARGS == ("filter", "order_by")


def test_connection_sidecar_inputs_from_kwargs_extracts_both():
    """Extraction reads the two kwarg keys (missing keys come back as ``None``)."""
    assert connection_sidecar_inputs_from_kwargs({"filter": "F", "order_by": "O"}) == ("F", "O")
    assert connection_sidecar_inputs_from_kwargs({}) == (None, None)


def test_connection_sidecar_inputs_reads_the_graphql_order_spelling():
    """The reader accepts BOTH order vocabularies (resolver kwargs vs walker args).

    The walker passes the converted selection's RAW GraphQL argument names, so
    the order sidecar arrives as ``orderBy`` under the default
    ``auto_camel_case``; the resolver passes Python ``**kwargs`` (``order_by``).
    Missing the camel spelling at plan time meant an ``orderBy:``-bearing
    nested connection window-planned a DEAD window and its recorded identity
    hid the per-parent fallback from strictness. The snake spelling wins when
    both are present (impossible in practice; pinned for determinism).
    """
    assert connection_sidecar_inputs_from_kwargs({"orderBy": "O"}) == (None, "O")
    assert connection_sidecar_inputs_from_kwargs({"order_by": "S", "orderBy": "C"}) == (None, "S")
    assert has_connection_sidecar_kwargs({"orderBy": "O"}) is True


def test_has_connection_sidecar_input_presence_predicate():
    """The presence predicate is True when EITHER input is non-``None``."""
    assert has_connection_sidecar_input(filter_input="F", order_by_input=None) is True
    assert has_connection_sidecar_input(filter_input=None, order_by_input="O") is True
    assert has_connection_sidecar_input(filter_input=None, order_by_input=None) is False


def test_has_connection_sidecar_kwargs_combines_extraction_and_predicate():
    """The kwargs predicate extracts then tests presence in one call."""
    assert has_connection_sidecar_kwargs({"filter": "F"}) is True
    assert has_connection_sidecar_kwargs({"order_by": "O"}) is True
    assert has_connection_sidecar_kwargs({"filter": None, "order_by": None}) is False
    assert has_connection_sidecar_kwargs({}) is False


# ---------------------------------------------------------------------------
# Count-free ``hasNextPage`` overfetch probe (the n+1 probe).
# ---------------------------------------------------------------------------


def test_fetch_mode_probes_on_plain_first_and_offset_pages_with_has_next_not_total():
    """``fetch_mode`` returns ``PROBED`` on the probe shapes when only hasNextPage is up.

    True for the plain ``first: N`` shape AND the bounded forward offset page
    (``offset > 0`` with a positive ``limit``) when ``hasNextPage`` is selected
    and ``totalCount`` is NOT (WS-A: the offset page composes the probe with its
    marker). ``COUNTED`` wins first when ``totalCount`` is observable, so probe
    XOR count holds.
    """
    for offset, limit in [(0, 3), (5, 3)]:
        plan = window_range_plan(offset=offset, limit=limit, reverse=False)
        assert plan.probe_shape is True
        assert plan.fetch_mode(has_next_selected=True, total_selected=False) is FetchMode.PROBED
        # totalCount observable -> the count is genuinely needed, no probe.
        assert plan.fetch_mode(has_next_selected=True, total_selected=True) is FetchMode.COUNTED
        # hasNextPage not selected on a bounded forward page -> NONE (no observer).
        assert plan.fetch_mode(has_next_selected=False, total_selected=False) is FetchMode.NONE
    # Non-probe shapes never probe, regardless of the selection: ``first: 0``,
    # reversed ``last:N``, and the unbounded forward page.
    for offset, limit, reverse in [
        (0, 0, False),
        (0, 3, True),
        (0, None, False),
        (5, None, False),
    ]:
        plan = window_range_plan(offset=offset, limit=limit, reverse=reverse)
        assert plan.probe_shape is False
        assert (
            plan.fetch_mode(has_next_selected=True, total_selected=False) is not FetchMode.PROBED
        )


def test_next_page_probe_field_honored_on_plain_first_and_offset_pages():
    """The ``next_page_probe`` kwarg is honored on the plain-first AND offset pages."""
    for offset, limit in [(0, 3), (5, 3)]:
        assert window_range_plan(
            offset=offset,
            limit=limit,
            reverse=False,
            next_page_probe=True,
        ).next_page_probe
    # Inert on the non-probe shapes even when the caller passes it through:
    # ``first: 0``, reversed ``last:N``, and the unbounded forward page.
    for offset, limit, reverse in [
        (0, 0, False),
        (0, 3, True),
        (0, None, False),
        (5, None, False),
    ]:
        plan = window_range_plan(
            offset=offset,
            limit=limit,
            reverse=reverse,
            next_page_probe=True,
        )
        assert plan.next_page_probe is False


def test_fetch_bounds_add_one_only_when_probe_active():
    """``fetch_upper_bound`` / ``fetch_limit`` add the single sentinel row iff probing.

    Equal to the PAGE bounds (``upper_bound`` / ``limit``) whenever the probe is
    off, so every existing renderer call site is untouched by construction. Both
    bounds add the SAME ``_probe_increment`` primitive (the single owner of the
    n+1 arithmetic), so they cannot drift.
    """
    off = window_range_plan(offset=0, limit=3, reverse=False)
    assert off._probe_increment == 0
    assert off.fetch_upper_bound == off.upper_bound == 3
    assert off.fetch_limit == off.limit == 3
    on = window_range_plan(offset=0, limit=3, reverse=False, next_page_probe=True)
    assert on._probe_increment == 1
    assert on.upper_bound == 3  # page bound unchanged
    assert on.limit == 3
    assert on.fetch_upper_bound == 4  # +1 sentinel
    assert on.fetch_limit == 4
    # Both derived bounds add the one shared increment - no independent ``+1``.
    assert on.fetch_upper_bound - on.upper_bound == on._probe_increment
    assert on.fetch_limit - on.limit == on._probe_increment


def test_fetch_bounds_are_none_for_an_unbounded_window():
    """An unbounded window (no ``first``) has no fetch ceiling - both bounds are None.

    The probe never engages on the unbounded shape, so an unbounded window
    carries no ``upper_bound`` / ``limit`` and both derived fetch bounds stay
    ``None`` (nothing for the ``_probe_increment`` to add to).
    """
    unbounded = window_range_plan(offset=0, limit=None, reverse=False)
    assert unbounded.upper_bound is None
    assert unbounded.limit is None
    assert unbounded.fetch_upper_bound is None
    assert unbounded.fetch_limit is None


def test_probe_composes_with_marker_but_never_with_count():
    """WS-A: probe and marker COMPOSE on the offset page; probe XOR count holds.

    The whole design now rests on ``next_page_probe`` XOR ``with_total_count``
    (the marker is a co-resident on the offset page, no longer a mutually-exclusive
    sibling): enforced across the window-shape input space, not merely asserted.
    On the plain first page the probe engages ALONE (no marker); on the bounded
    forward offset page it engages WITH the marker.
    """
    for offset in (0, 1, 5):
        for limit in (
            0,
            1,
            3,
            None,
        ):
            for reverse in (False, True):
                plan = window_range_plan(
                    offset=offset,
                    limit=limit,
                    reverse=reverse,
                    next_page_probe=True,
                )
                # An engaged probe is always safe to leave count-free (probe XOR
                # count) - the shared invariant never rejects a count-free probe.
                if plan.next_page_probe:
                    assert_window_fetch_mode(plan, with_total_count=False)
                probes = (
                    plan.fetch_mode(has_next_selected=True, total_selected=False)
                    is FetchMode.PROBED
                )
                if probes:
                    # Plain first page probes alone; the bounded offset page
                    # composes the probe with its marker row.
                    if plan.plain_first_page:
                        assert plan.add_marker_rows is False
                    else:
                        assert plan.offset > 0
                        assert plan.add_marker_rows is True


def test_assert_window_fetch_mode_rejects_engaged_probe_with_count():
    """An engaged probe window carrying the count is a rejected planner bug.

    The probe answers ``hasNextPage`` from an overfetched sentinel; a count
    annotation makes the resolver treat that sentinel as a real edge. On a
    probe-eligible shape (the plain first page OR the bounded forward offset page)
    the two fetch modes are mutually exclusive and the contract raises loudly -
    never normalizes.
    """
    for offset in (0, 5):
        engaged = window_range_plan(offset=offset, limit=3, reverse=False, next_page_probe=True)
        assert engaged.next_page_probe is True
        with pytest.raises(OptimizerError, match="mutually exclusive"):
            assert_window_fetch_mode(engaged, with_total_count=True)
        # The probe alone (no count) is the legitimate count-free shape.
        assert_window_fetch_mode(engaged, with_total_count=False)


def test_assert_window_fetch_mode_allows_count_without_probe():
    """A counted window with no engaged probe is the ordinary shape - allowed."""
    plain = window_range_plan(offset=0, limit=3, reverse=False)
    assert plain.next_page_probe is False
    assert_window_fetch_mode(plain, with_total_count=True)


def test_assert_window_fetch_mode_for_allows_inert_off_shape_probe_with_count():
    """The RAW-flag pair is fine off any probe-eligible shape (the probe is inert).

    ``window_range_plan`` drops ``next_page_probe`` off the probe-eligible shapes
    (plain first page and bounded forward offset page), so an unbounded offset
    window (``after`` with no ``first``) passed both flags never overfetches and
    must not be rejected - the contract keys on the EFFECTIVE probe, not the raw
    request flags.
    """
    assert_window_fetch_mode_for(
        offset=2,
        limit=None,
        reverse=False,
        with_total_count=True,
        next_page_probe=True,
    )
    # The same params on the bounded offset page DO engage the probe -> reject.
    with pytest.raises(OptimizerError, match="mutually exclusive"):
        assert_window_fetch_mode_for(
            offset=2,
            limit=3,
            reverse=False,
            with_total_count=True,
            next_page_probe=True,
        )


def _rows(*row_numbers):
    return [SimpleNamespace(rn=n) for n in row_numbers]


def test_split_window_rows_marker_offset_shape_drops_the_marker():
    """Ambiguous ``after:`` shape: rows at or below the offset are dropped markers."""
    plan = window_range_plan(offset=5, limit=2, reverse=False)
    assert plan.add_marker_rows is True
    page_rows, probe_seen = split_window_rows(_rows(1, 6, 7), plan, row_number="rn")
    assert [r.rn for r in page_rows] == [6, 7]
    assert probe_seen is False


def test_split_window_rows_first_zero_shape_has_no_page():
    """``first: 0`` marker shape: the marker is kept in SQL but the page is empty."""
    plan = window_range_plan(offset=0, limit=0, reverse=False)
    assert plan.add_marker_rows is True
    page_rows, probe_seen = split_window_rows(_rows(1), plan, row_number="rn")
    assert page_rows == []
    assert probe_seen is False


def test_split_window_rows_probe_shape_reports_and_drops_the_sentinel():
    """Probe shape: rows past ``upper_bound`` are the dropped sentinel = ``hasNextPage``."""
    plan = window_range_plan(offset=0, limit=3, reverse=False, next_page_probe=True)
    # A full page plus the overfetched sentinel row (rn 4).
    page_rows, probe_seen = split_window_rows(_rows(1, 2, 3, 4), plan, row_number="rn")
    assert [r.rn for r in page_rows] == [1, 2, 3]
    assert probe_seen is True
    # A short page (no sentinel) -> no next page.
    page_rows, probe_seen = split_window_rows(_rows(1, 2), plan, row_number="rn")
    assert [r.rn for r in page_rows] == [1, 2]
    assert probe_seen is False


def test_split_window_rows_plain_shape_passes_rows_through():
    """A non-marker, non-probe window returns every row and no sentinel."""
    plan = window_range_plan(offset=0, limit=3, reverse=False)
    assert plan.add_marker_rows is False
    assert plan.next_page_probe is False
    page_rows, probe_seen = split_window_rows(_rows(1, 2, 3), plan, row_number="rn")
    assert [r.rn for r in page_rows] == [1, 2, 3]
    assert probe_seen is False


def test_split_window_rows_composed_offset_probe_drops_marker_and_sentinel():
    """WS-A composed offset page: the marker (rn 1) AND the probe sentinel drop.

    ``after:`` offset 5, ``first: 2`` with the probe engaged fetches the abs-first
    marker (rn 1), the page rows (rn 6, 7), and the sentinel (rn 8 ==
    ``fetch_upper_bound`` == ``upper_bound`` 7 + 1). The page proper is
    ``offset < rn <= upper_bound`` and ``probe_row_seen`` reports the sentinel.
    """
    plan = window_range_plan(offset=5, limit=2, reverse=False, next_page_probe=True)
    assert plan.add_marker_rows is True
    assert plan.next_page_probe is True
    assert plan.upper_bound == 7
    assert plan.fetch_upper_bound == 8
    # Full page plus the marker and the sentinel -> hasNextPage True.
    page_rows, probe_seen = split_window_rows(_rows(1, 6, 7, 8), plan, row_number="rn")
    assert [r.rn for r in page_rows] == [6, 7]
    assert probe_seen is True
    # Full page, marker present, no sentinel -> hasNextPage False (partition ends
    # exactly at offset+limit).
    page_rows, probe_seen = split_window_rows(_rows(1, 6, 7), plan, row_number="rn")
    assert [r.rn for r in page_rows] == [6, 7]
    assert probe_seen is False
    # Marker-only overshoot (all children at or before the offset) -> empty page,
    # no sentinel.
    page_rows, probe_seen = split_window_rows(_rows(1), plan, row_number="rn")
    assert page_rows == []
    assert probe_seen is False


@pytest.mark.parametrize(
    (
        "offset",
        "limit",
        "reverse",
        "expect_marker",
        "expect_probe",
        "expect_mode",
    ),
    [
        # plain first:N -> probe eligible, no marker; hasNext-only -> PROBED.
        (
            0,
            3,
            False,
            False,
            True,
            FetchMode.PROBED,
        ),
        # offset page (offset>0, bounded) -> marker AND probe compose -> PROBED.
        (
            5,
            3,
            False,
            True,
            True,
            FetchMode.PROBED,
        ),
        # first:0 -> marker, no probe; the marker shape is always COUNTED.
        (
            0,
            0,
            False,
            True,
            False,
            FetchMode.COUNTED,
        ),
        # unbounded forward -> no marker at offset 0, no probe -> CONSTANT_FALSE.
        (
            0,
            None,
            False,
            False,
            False,
            FetchMode.CONSTANT_FALSE,
        ),
        # unbounded offset -> marker (ambiguous), no probe -> CONSTANT_FALSE.
        (
            5,
            None,
            False,
            True,
            False,
            FetchMode.CONSTANT_FALSE,
        ),
        # reverse last:N -> no marker, no probe -> CONSTANT_FALSE (partition tail).
        (
            0,
            3,
            True,
            False,
            False,
            FetchMode.CONSTANT_FALSE,
        ),
    ],
)
def test_window_range_plan_mode_table(
    offset,
    limit,
    reverse,
    expect_marker,
    expect_probe,
    expect_mode,
):
    """WS-A post-change decision table for ``window_range_plan`` (probe passed on).

    Pins the composed offset-page shape (marker AND probe both set), the
    probe-eligible plain first page, and the count-forcing / constant-False shapes
    that never probe. The centralized ``fetch_mode`` (the single ``FetchMode``
    source of truth) is asserted under the count-free-preferring observer set
    (``hasNextPage`` selected, ``totalCount`` not) so each shape's distinct mode
    is visible; ``totalCount`` would collapse every row to ``COUNTED``.
    """
    plan = window_range_plan(offset=offset, limit=limit, reverse=reverse, next_page_probe=True)
    assert plan.add_marker_rows is expect_marker
    assert plan.next_page_probe is expect_probe
    assert plan.fetch_mode(has_next_selected=True, total_selected=False) is expect_mode


#: The canonical fetch-mode contract: each ``FetchMode`` maps to exactly one
#: ``(with_total_count, next_page_probe, serves_constant_false_has_next_page)``
#: triple. The planner reads the first two off the mode; the resolver reads the
#: constant-False shape at resolve time. Pinned here so a future edit to the
#: single source cannot silently re-point a mode at a different triple.
_FETCH_MODE_TRIPLE = {
    FetchMode.COUNTED: (True, False, False),
    FetchMode.PROBED: (False, True, False),
    FetchMode.CONSTANT_FALSE: (False, False, True),
    FetchMode.NONE: (False, False, False),
}


@pytest.mark.parametrize(
    (
        "plan",
        "has_next_selected",
        "total_selected",
        "expected_mode",
    ),
    [
        # COUNTED: totalCount observed on a plain first page.
        (
            window_range_plan(offset=0, limit=3, reverse=False),
            True,
            True,
            FetchMode.COUNTED,
        ),
        # COUNTED: the ``first: 0`` marker shape, no observers needed.
        (
            window_range_plan(offset=0, limit=0, reverse=False),
            False,
            False,
            FetchMode.COUNTED,
        ),
        # PROBED: bounded forward offset page, hasNextPage only.
        (
            window_range_plan(offset=5, limit=3, reverse=False),
            True,
            False,
            FetchMode.PROBED,
        ),
        # CONSTANT_FALSE: unbounded forward page, hasNextPage only.
        (
            window_range_plan(offset=0, limit=None, reverse=False),
            True,
            False,
            FetchMode.CONSTANT_FALSE,
        ),
        # CONSTANT_FALSE: reversed last:N page (the partition tail).
        (
            window_range_plan(offset=0, limit=3, reverse=True),
            True,
            False,
            FetchMode.CONSTANT_FALSE,
        ),
        # NONE: edges-only bounded forward page (no count-derived observer).
        (
            window_range_plan(offset=0, limit=3, reverse=False),
            False,
            False,
            FetchMode.NONE,
        ),
    ],
)
def test_fetch_mode_maps_to_the_count_probe_constant_false_triple(
    plan,
    has_next_selected,
    total_selected,
    expected_mode,
):
    """Each ``FetchMode`` resolves to exactly one (count, probe, constant_false) triple.

    The single source of truth: the planner derives ``with_total_count`` from
    ``COUNTED`` and ``next_page_probe`` from ``PROBED`` (probe XOR count), and the
    resolver reads ``constant_false_shape`` for the ``CONSTANT_FALSE`` mode. This
    pins the whole taxonomy in one place so the centralization cannot drift.
    """
    mode = plan.fetch_mode(has_next_selected=has_next_selected, total_selected=total_selected)
    assert mode is expected_mode
    want_count, want_probe, want_constant_false = _FETCH_MODE_TRIPLE[mode]
    # Planner derivation - both flags come from the ONE mode value.
    assert (mode is FetchMode.COUNTED) is want_count
    assert (mode is FetchMode.PROBED) is want_probe
    # probe XOR count is the standing invariant.
    assert not (want_count and want_probe)
    # The mode's shared SHAPE predicates the resolver reads off the rows.
    if want_probe:
        assert plan.probe_shape is True
    if want_constant_false:
        assert plan.constant_false_shape is True
