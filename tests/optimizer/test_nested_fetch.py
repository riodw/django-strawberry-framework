"""Tests for the nested-connection fetch-strategy seam (``optimizer/nested_fetch.py``).

The seam contract: the walker rules out every strategy-independent fallback
shape, then hands one ``NestedConnectionRequest`` to the active strategy;
``WindowedPrefetchStrategy`` (the default) must reproduce the spec-033
windowed prefetch byte-for-byte (the existing walker/plans/connection pins
run unchanged - the seam's Definition of Done); strategy selection is fixed
per extension instance and published per execution via a ``ContextVar``.
"""

from types import SimpleNamespace

import pytest
from apps.library.models import Genre
from django.db.models import Prefetch

from django_strawberry_framework import DjangoOptimizerExtension
from django_strawberry_framework.exceptions import ConfigurationError, OptimizerError
from django_strawberry_framework.optimizer.nested_fetch import (
    WINDOWED_STRATEGY,
    WindowedPrefetchStrategy,
    _active_strategy,
    _strategy_for_vendor,
    active_strategy,
    resolve_strategy,
)
from django_strawberry_framework.optimizer.plans import (
    WINDOW_ROW_NUMBER,
    WINDOW_TOTAL_COUNT,
    OptimizationPlan,
)
from tests.optimizer._builders import nested_connection_request


def _books_request(**overrides):
    """A minimal valid request for the reverse-M2M ``Genre.books`` relation."""
    return nested_connection_request(Genre, "books", **overrides)


def test_windowed_strategy_attaches_windowed_prefetch():
    """The default strategy lands the spec-033 shape: windowed qs on the ``to_attr``."""
    plan = OptimizationPlan()
    assert WindowedPrefetchStrategy().plan(_books_request(), plan) is True
    (entry,) = plan.prefetch_related
    assert isinstance(entry, Prefetch)
    assert entry.prefetch_through == "books"
    assert entry.to_attr == "_dst_books_connection"
    annotations = entry.queryset.query.annotations
    assert WINDOW_ROW_NUMBER in annotations
    assert WINDOW_TOTAL_COUNT in annotations


def test_request_rejects_engaged_probe_with_count():
    """The strategy seam rejects an engaged-probe request that also wants the count.

    ``NestedConnectionRequest`` is the boundary every strategy consumes, so its
    construction enforces the probe/count mutual-exclusion (the shared
    ``assert_window_fetch_mode_for``): a plain-first-page request (offset 0,
    ``limit`` > 0) with ``next_page_probe=True`` cannot also carry
    ``with_total_count=True``. The walker never emits this pair; a future
    strategy or direct caller that does fails loudly here.
    """
    with pytest.raises(OptimizerError, match="mutually exclusive"):
        _books_request(with_total_count=True, next_page_probe=True)


def test_windowed_strategy_honors_conditional_count():
    """``with_total_count=False`` flows through the request to the window."""
    plan = OptimizationPlan()
    WindowedPrefetchStrategy().plan(_books_request(with_total_count=False), plan)
    (entry,) = plan.prefetch_related
    assert WINDOW_TOTAL_COUNT not in entry.queryset.query.annotations


def test_strategy_for_vendor_prefers_lateral_on_postgres():
    """The pure ``"auto"`` mapping: Postgres goes lateral, everyone else windows."""
    assert _strategy_for_vendor("postgresql") == "lateral"
    assert _strategy_for_vendor("sqlite") == "windowed"
    assert _strategy_for_vendor("mysql") == "windowed"


def test_resolve_strategy_by_name_auto_and_instance():
    """Names resolve from the registry; ``"auto"`` sniffs the default vendor;
    instances pass through."""
    from django.db import connection

    from django_strawberry_framework.optimizer.lateral_fetch import LATERAL_STRATEGY

    assert resolve_strategy("windowed") is WINDOWED_STRATEGY
    # ``auto`` follows the live vendor: lateral on the pg tier, windowed on
    # the sqlite coverage tier (``_strategy_for_vendor`` pins the pure map).
    expected = LATERAL_STRATEGY if connection.vendor == "postgresql" else WINDOWED_STRATEGY
    assert resolve_strategy("auto") is expected
    custom = SimpleNamespace(name="custom", plan=lambda request, plan: False)
    assert resolve_strategy(custom) is custom


def test_resolve_strategy_rejects_unknown_name_and_bad_type():
    """Typos fail loud at construction, never at query time."""
    with pytest.raises(
        ConfigurationError,
        match="Unknown nested_connection_strategy 'correlated'",
    ):
        resolve_strategy("correlated")
    with pytest.raises(ConfigurationError, match="plan\\(request, plan\\) method"):
        resolve_strategy(42)


def test_resolve_strategy_lateral_loads_the_lateral_backend():
    """``"lateral"`` lazily registers and returns the Postgres backend singleton."""
    from django_strawberry_framework.optimizer.lateral_fetch import LATERAL_STRATEGY

    assert resolve_strategy("lateral") is LATERAL_STRATEGY
    assert resolve_strategy("lateral") is LATERAL_STRATEGY  # registry, not re-import


def test_resolve_strategy_none_reads_setting(settings):
    """``None`` defers to ``DJANGO_STRAWBERRY_FRAMEWORK["NESTED_CONNECTION_STRATEGY"]``."""
    assert resolve_strategy(None) is WINDOWED_STRATEGY  # key absent -> default
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"NESTED_CONNECTION_STRATEGY": "windowed"}
    assert resolve_strategy(None) is WINDOWED_STRATEGY
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"NESTED_CONNECTION_STRATEGY": "nope"}
    with pytest.raises(ConfigurationError, match="Unknown nested_connection_strategy 'nope'"):
        resolve_strategy(None)


def test_extension_pins_strategy_at_construction():
    """The kwarg resolves eagerly; the instance carries its strategy."""
    extension = DjangoOptimizerExtension()
    assert extension.nested_connection_strategy is WINDOWED_STRATEGY
    custom = SimpleNamespace(name="custom", plan=lambda request, plan: False)
    assert (
        DjangoOptimizerExtension(nested_connection_strategy=custom).nested_connection_strategy
        is custom
    )
    with pytest.raises(ConfigurationError):
        DjangoOptimizerExtension(nested_connection_strategy="correlated")


def test_active_strategy_defaults_windowed_and_reads_contextvar():
    """Direct ``plan_optimizations`` callers get windowed; executions get the published one."""
    assert active_strategy() is WINDOWED_STRATEGY
    custom = SimpleNamespace(name="custom", plan=lambda request, plan: True)
    token = _active_strategy.set(custom)
    try:
        assert active_strategy() is custom
    finally:
        _active_strategy.reset(token)
    assert active_strategy() is WINDOWED_STRATEGY


def test_on_execute_publishes_instance_strategy():
    """``on_execute`` publishes the instance's strategy for the walker's lifetime."""
    custom = SimpleNamespace(name="custom", plan=lambda request, plan: True)
    extension = DjangoOptimizerExtension(nested_connection_strategy=custom)
    hook = extension.on_execute()
    next(hook)  # enter the execution window
    try:
        assert active_strategy() is custom
    finally:
        with pytest.raises(StopIteration):
            next(hook)  # exit; the finally block resets the ContextVar
    assert active_strategy() is WINDOWED_STRATEGY


def test_unwindowable_child_queryset_reason_matrix():
    """The strategy-independent safety classifier (feedback2 P0-3).

    Each unsafe consumer-hook shape maps to a stable reason; a plain
    queryset (with or without projection/ordering) maps to ``None``.
    """
    from apps.library.models import Book

    from django_strawberry_framework.optimizer.nested_fetch import (
        unwindowable_child_queryset_reason,
    )

    assert unwindowable_child_queryset_reason(Book.objects.all()[:10]) == "sliced"
    assert (
        unwindowable_child_queryset_reason(Book.objects.select_for_update()) == "select_for_update"
    )
    assert (
        unwindowable_child_queryset_reason(
            Book.objects.filter(pk=1).union(Book.objects.filter(pk=2)),
        )
        == "combined"
    )
    assert unwindowable_child_queryset_reason(Book.objects.distinct()) == "distinct"
    assert unwindowable_child_queryset_reason(Book.objects.values_list("id")) == "values"
    assert unwindowable_child_queryset_reason(Book.objects.only("id", "title")) is None
    assert unwindowable_child_queryset_reason(Book.objects.order_by("title")) is None
