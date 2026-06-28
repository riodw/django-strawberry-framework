"""Tests for the shared fail-loud converter-dispatch skeleton (``utils/converters.py``, spec-039 P1.4).

``convert_with_mro`` single-sites the ordered-precheck -> MRO-walk ->
raising-fallthrough control flow both ``forms/converter.py`` and
``rest_framework/serializer_converter.py`` ride. These tests pin the skeleton in
isolation (flavor-free) so the no-silent-catch-all contract is verified once at
its owner:

- a precheck match wins (and runs in order; a precheck for a parent class
  precedes the scalar walk over a child);
- the MRO registry resolves the MOST-specific class regardless of insertion
  order;
- an unhandled field calls the ``fallthrough_error_factory`` and raises.
"""

from __future__ import annotations

import pytest

from django_strawberry_framework.utils.converters import convert_with_mro


class _Base:
    pass


class _Child(_Base):
    pass


def test_precheck_match_wins_over_registry():
    """An ``isinstance`` precheck match returns before the scalar registry walk runs.

    ``_Child`` subclasses ``_Base``; a precheck on ``_Base`` must win even though
    ``_Child`` is also in the registry (the more-specific kind detection precedes
    the walk - the relation/file/multi-choice ordering both flavors rely on).
    """
    field = _Child()
    result = convert_with_mro(
        field,
        isinstance_prechecks=[(_Base, lambda _f: "precheck-won")],
        scalar_registry={_Child: "registry-value"},
        fallthrough_error_factory=lambda _f: AssertionError("should not raise"),
    )
    assert result == "precheck-won"


def test_prechecks_run_in_order():
    """The FIRST matching precheck wins (ordered, not most-specific)."""
    field = _Child()
    result = convert_with_mro(
        field,
        isinstance_prechecks=[(_Child, lambda _f: "first"), (_Base, lambda _f: "second")],
        scalar_registry={},
        fallthrough_error_factory=lambda _f: AssertionError("should not raise"),
    )
    assert result == "first"


def test_precheck_returning_none_continues_to_walk():
    """A precheck handler returning ``None`` lets the skeleton continue to the registry walk.

    This is the bare-``forms.Field`` exact-type pattern: a precheck that matches by
    ``isinstance`` but returns ``None`` for the non-exact case falls through to the
    scalar walk rather than short-circuiting.
    """
    field = _Child()
    result = convert_with_mro(
        field,
        isinstance_prechecks=[(_Base, lambda _f: None)],
        scalar_registry={_Child: "registry-value"},
        fallthrough_error_factory=lambda _f: AssertionError("should not raise"),
    )
    assert result == "registry-value"


def test_mro_walk_resolves_most_specific_class():
    """The MRO walk resolves the field's OWN class before a registered parent.

    ``_Child`` and ``_Base`` are both registered; the walk visits ``_Child`` first
    (the field's own class), so it resolves to ``_Child``'s value regardless of
    insertion order (the ``FloatField`` / ``DecimalField`` non-collapse guarantee).
    """
    field = _Child()
    # Insert the parent FIRST to prove insertion order does not decide the winner.
    result = convert_with_mro(
        field,
        isinstance_prechecks=[],
        scalar_registry={_Base: "base-value", _Child: "child-value"},
        fallthrough_error_factory=lambda _f: AssertionError("should not raise"),
    )
    assert result == "child-value"


def test_mro_walk_resolves_unregistered_subclass_to_parent():
    """An UNregistered subclass resolves to its registered parent's value (the EmailField-under-CharField shape)."""
    field = _Child()
    result = convert_with_mro(
        field,
        isinstance_prechecks=[],
        scalar_registry={_Base: "base-value"},  # only the parent is registered
        fallthrough_error_factory=lambda _f: AssertionError("should not raise"),
    )
    assert result == "base-value"


def test_unhandled_field_raises_via_factory():
    """A field matched by neither path calls ``fallthrough_error_factory`` and raises it.

    The load-bearing no-catch-all contract: there is NO base-class fallback that
    silently coerces an unknown field; the factory's exception is raised.
    """

    class _Unrelated:
        pass

    def _factory(field):
        return ValueError(f"unsupported: {type(field).__name__}")

    with pytest.raises(ValueError, match="unsupported: _Unrelated"):
        convert_with_mro(
            _Unrelated(),
            isinstance_prechecks=[(_Base, lambda _f: "won't match")],
            scalar_registry={_Child: "won't match"},
            fallthrough_error_factory=_factory,
        )
