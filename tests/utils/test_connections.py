"""Unit tests for the shared connection planner/resolver contracts.

Covers ``django_strawberry_framework/utils/connections.py`` -- the cycle-safe
home for the slice-window derivation and the sidecar-kwarg family that the
optimizer walker (plan time) and the Relay resolver (resolve time) must spell
identically.
"""

import pytest
from strawberry.relay.types import to_base64
from strawberry.relay.utils import SliceMetadata

from django_strawberry_framework.utils.connections import (
    CONNECTION_FILTER_KWARG,
    CONNECTION_ORDER_KWARG,
    CONNECTION_SIDECAR_KWARGS,
    ConnectionWindowBounds,
    UnwindowableConnection,
    connection_sidecar_inputs_from_kwargs,
    derive_connection_window_bounds,
    has_connection_sidecar_input,
    has_connection_sidecar_kwargs,
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
