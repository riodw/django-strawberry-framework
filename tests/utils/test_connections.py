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


def test_sidecar_kwarg_family_constants():
    """The sidecar kwarg family is the Python kwarg names ``filter`` / ``order_by``."""
    assert CONNECTION_FILTER_KWARG == "filter"
    assert CONNECTION_ORDER_KWARG == "order_by"
    assert CONNECTION_SIDECAR_KWARGS == ("filter", "order_by")


def test_connection_sidecar_inputs_from_kwargs_extracts_both():
    """Extraction reads the two kwarg keys (missing keys come back as ``None``)."""
    assert connection_sidecar_inputs_from_kwargs({"filter": "F", "order_by": "O"}) == ("F", "O")
    assert connection_sidecar_inputs_from_kwargs({}) == (None, None)


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


def test_next_page_probe_only_on_plain_first_page_with_has_next_not_total():
    """``wants_next_page_probe`` is the shape+selection gate for the probe.

    True only for the plain ``first: N`` shape when ``hasNextPage`` is selected
    and ``totalCount`` is NOT; the internal ``plain_first_page`` re-check makes
    it self-normalizing and safe to call on any plan.
    """
    plain = window_range_plan(offset=0, limit=3, reverse=False)
    assert plain.plain_first_page is True
    assert plain.wants_next_page_probe(has_next_selected=True, total_selected=False) is True
    # totalCount observable -> the count is genuinely needed, no probe.
    assert plain.wants_next_page_probe(has_next_selected=True, total_selected=True) is False
    # hasNextPage not selected -> nothing to serve from the sentinel.
    assert plain.wants_next_page_probe(has_next_selected=False, total_selected=False) is False
    # Non-plain shapes never probe, regardless of the selection.
    for offset, limit, reverse in [
        (5, 3, False),
        (0, 0, False),
        (0, 3, True),
        (0, None, False),
    ]:
        plan = window_range_plan(offset=offset, limit=limit, reverse=reverse)
        assert plan.wants_next_page_probe(has_next_selected=True, total_selected=False) is False


def test_next_page_probe_field_normalized_to_plain_first_page():
    """The ``next_page_probe`` kwarg is honored only on the ``plain_first_page`` shape."""
    assert window_range_plan(
        offset=0,
        limit=3,
        reverse=False,
        next_page_probe=True,
    ).next_page_probe
    # Inert everywhere else even when the caller passes it through.
    for offset, limit, reverse in [
        (5, 3, False),
        (0, 0, False),
        (0, 3, True),
        (0, None, False),
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

    The probe never engages off the plain-first-page shape, so an unbounded
    window carries no ``upper_bound`` / ``limit`` and both derived fetch bounds
    stay ``None`` (nothing for the ``_probe_increment`` to add to).
    """
    unbounded = window_range_plan(offset=0, limit=None, reverse=False)
    assert unbounded.upper_bound is None
    assert unbounded.limit is None
    assert unbounded.fetch_upper_bound is None
    assert unbounded.fetch_limit is None


def test_probe_and_marker_shapes_are_mutually_exclusive():
    """``next_page_probe`` and ``add_marker_rows`` are never both true.

    The property the whole design rests on (the probe is a sibling sentinel to
    the marker row, never a co-resident): enforced across the window-shape input
    space, not merely asserted. ``wants_next_page_probe`` likewise never fires
    on a marker shape.
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
                assert not (plan.add_marker_rows and plan.next_page_probe)
                if plan.wants_next_page_probe(has_next_selected=True, total_selected=False):
                    assert plan.add_marker_rows is False
                    assert plan.plain_first_page is True


def test_assert_window_fetch_mode_rejects_engaged_probe_with_count():
    """An engaged probe window carrying the count is a rejected planner bug.

    The probe answers ``hasNextPage`` from an overfetched sentinel; a count
    annotation makes the resolver treat that sentinel as a real edge. On the
    ``plain_first_page`` shape (where the probe engages) the two fetch modes are
    mutually exclusive and the contract raises loudly - never normalizes.
    """
    engaged = window_range_plan(offset=0, limit=3, reverse=False, next_page_probe=True)
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
    """The RAW-flag pair is fine off the plain-first-page shape (the probe is inert).

    ``window_range_plan`` drops ``next_page_probe`` off the ``plain_first_page``
    shape, so an ``after``-offset window passed both flags never overfetches and
    must not be rejected - the contract keys on the EFFECTIVE probe, not the raw
    request flags (guarding the off-shape unit path in
    ``test_plans.py::test_next_page_probe_ignored_off_the_plain_first_page_shape``).
    """
    assert_window_fetch_mode_for(
        offset=2,
        limit=3,
        reverse=False,
        with_total_count=True,
        next_page_probe=True,
    )
    # The same params on the plain-first-page shape DO engage the probe -> reject.
    with pytest.raises(OptimizerError, match="mutually exclusive"):
        assert_window_fetch_mode_for(
            offset=0,
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
