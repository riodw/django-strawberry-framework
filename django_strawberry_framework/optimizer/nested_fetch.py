"""Pluggable nested-connection fetch strategies (the Prisma-style seam).

How a recognized nested Relay connection is FETCHED is a strategy, not the
optimizer's identity (the lesson from Prisma's ``JoinSelectBuilder`` trait:
one stable plan interface, swappable SQL shapes behind it). The walker
(``optimizer/walker.py::_plan_connection_relation``) owns everything
strategy-independent - recognition, the Decision-6 fallback shapes (sidecar,
divergent aliases, ``OptimizerHint.SKIP``, DISTINCT, malformed slice,
unwindowable partition), child-queryset construction, the deterministic
order, and the slice window - then hands one ``NestedConnectionRequest`` to
the active strategy, which attaches its fetch directives to the plan.

The default (and today only) strategy is ``WindowedPrefetchStrategy`` - the
verbatim spec-033 windowed prefetch: ``apply_window_pagination`` over the
child queryset, carried as a ``Prefetch(..., to_attr="_dst_<field>_connection")``.
Any strategy that lands an ordered list of model instances carrying
``_dst_row_number`` (and ``_dst_total_count`` when the request wants it)
under ``request.to_attr`` inherits the ENTIRE connection fast path
(``connection.py::_resolve_from_window`` - cursor parity, marker
classification, strictness) without touching ``connection.py``. The Postgres
``CROSS JOIN LATERAL`` strategy (``optimizer/lateral_fetch.py``) is the
second backend; its rows satisfy exactly that contract.

Strategy selection is fixed per ``DjangoOptimizerExtension`` INSTANCE at
construction (``nested_connection_strategy=`` kwarg, falling back to the
``DJANGO_STRAWBERRY_FRAMEWORK["NESTED_CONNECTION_STRATEGY"]`` setting, then
``"windowed"``). The plan cache is instance-bound, so one cache never mixes
plans from two strategies; ``"auto"`` resolves from the default DB vendor
eagerly at construction for the same reason. The walker reaches the active
instance's strategy through a ``ContextVar`` the extension publishes in
``on_execute`` - direct ``plan_optimizations`` callers (tests) get the
windowed default.
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Protocol

from django.db.models import Prefetch
from django.db.models.query import ModelIterable

from ..exceptions import ConfigurationError
from .join_taxonomy import RelationJoinDescriptor
from .plans import OptimizationPlan, append_prefetch_unique, apply_window_pagination


def unwindowable_child_queryset_reason(queryset: Any) -> str | None:
    """Classify child-queryset states NO fetch strategy can window safely.

    The strategy-independent safety gate the walker runs before building a
    ``NestedConnectionRequest`` (feedback2 P0-3): these shapes come from
    consumer hooks (a target ``get_queryset`` returning a pre-shaped
    queryset) and either crash inside ``apply_window_pagination`` before any
    fallback could help, or silently change semantics under raw SQL:

    - ``sliced``: ``.order_by()`` on a sliced queryset raises ``TypeError:
      Cannot reorder a query once a slice has been taken`` - a deep Django
      error, not a package fallback.
    - ``select_for_update``: a locking queryset must not have its lock
      silently dropped by the lateral raw-SQL path (and a locked window
      scan is never what the consumer meant).
    - ``combined``: union/intersection/difference querysets cannot take
      window annotations or per-partition filters.
    - ``distinct``: the window ``Count(1) OVER`` would over-count
      pre-DISTINCT rows (the historical Decision-6 shape 4 guard, now
      centralized here).
    - ``values``: a ``values()``/``values_list()`` iterable has no model
      instances to carry the window attributes.

    Returns a short reason string (stable, test/telemetry-friendly) or
    ``None`` for a plain windowable queryset. The walker treats any reason
    as a fully-unplanned Decision-6 fallback: no prefetch, no resolver keys,
    so the per-parent resolution stays strictness-visible and any truly
    invalid consumer shape raises ITS OWN error at the field with normal
    error locality.
    """
    query = getattr(queryset, "query", None)
    if getattr(query, "is_sliced", False):
        return "sliced"
    if getattr(query, "select_for_update", False):
        return "select_for_update"
    if getattr(query, "combinator", None):
        return "combined"
    if getattr(query, "distinct", False):
        return "distinct"
    if getattr(queryset, "_iterable_class", ModelIterable) is not ModelIterable:
        return "values"
    return None


@dataclass(frozen=True)
class NestedConnectionRequest:
    """Everything the walker resolved about one plannable nested connection.

    Built only AFTER every strategy-independent fallback shape has been ruled
    out: ``django_field`` is the RAW Django relation field/rel (the walker's
    ``_raw_relation_field``, not a ``FieldMeta`` - strategies may need
    ``remote_field`` / through metadata only the raw descriptor carries),
    ``child_queryset`` already carries the child plan (``only`` /
    ``select_related`` / nested prefetches / visibility hook), ``join`` is
    the relation's ``classify_relation_join`` descriptor (``windowable`` is
    ``True`` by construction here), ``order_by`` is the deterministic total
    order shared with resolve time, and ``(offset, limit, reverse,
    with_total_count)`` is the slice window. ``to_attr`` / ``lookup`` are the
    attach contract: the strategy's rows must land under ``to_attr`` on each
    parent reached via ``lookup``.
    """

    django_field: Any
    relation_field_name: str
    prefix: str
    child_queryset: Any
    join: RelationJoinDescriptor
    order_by: tuple[Any, ...]
    offset: int
    limit: int | None
    reverse: bool
    with_total_count: bool
    to_attr: str
    lookup: str


class NestedConnectionStrategy(Protocol):
    """One way to fetch a nested connection's per-parent pages.

    ``plan`` attaches fetch directives for ``request`` to ``plan`` and
    returns ``True``; returning ``False`` leaves the selection UNPLANNED
    (the walker then records no resolver identities, so the per-parent
    access stays visible to strictness - the Decision-6 fallback
    discipline). Implementations must satisfy the ``to_attr`` row contract
    described in the module docstring.
    """

    name: str

    def plan(self, request: NestedConnectionRequest, plan: OptimizationPlan) -> bool:
        """Attach fetch directives for one nested connection; ``True`` = planned."""


class WindowedPrefetchStrategy:
    """The default: spec-033's windowed prefetch, moved verbatim from the walker."""

    name = "windowed"

    def plan(self, request: NestedConnectionRequest, plan: OptimizationPlan) -> bool:
        """Window the child queryset and carry it as a ``to_attr`` Prefetch."""
        windowed_queryset = apply_window_pagination(
            request.child_queryset,
            partition_by=request.join.partition_expr,
            order_by=request.order_by,
            offset=request.offset,
            limit=request.limit,
            reverse=request.reverse,
            with_total_count=request.with_total_count,
        )
        append_prefetch_unique(
            plan.prefetch_related,
            Prefetch(
                request.lookup,
                queryset=windowed_queryset,
                to_attr=request.to_attr,
            ),
        )
        return True


#: The shared default-strategy singleton (stateless, so one instance serves
#: every extension and every direct ``plan_optimizations`` caller).
WINDOWED_STRATEGY = WindowedPrefetchStrategy()

#: Registered built-in strategies by name. ``"lateral"`` loads lazily via
#: ``_builtin_strategies`` - ``lateral_fetch`` imports THIS module for the
#: request/protocol types, so the registration cannot be a top-level import.
_STRATEGIES: dict[str, NestedConnectionStrategy] = {"windowed": WINDOWED_STRATEGY}


def _builtin_strategies() -> dict[str, NestedConnectionStrategy]:
    """The full built-in registry, importing the lateral backend on first use."""
    if "lateral" not in _STRATEGIES:
        from .lateral_fetch import LATERAL_STRATEGY

        _STRATEGIES["lateral"] = LATERAL_STRATEGY
    return _STRATEGIES


def _strategy_for_vendor(vendor: str) -> str:
    """Map a DB vendor string to the preferred built-in strategy name.

    The ``"auto"`` resolver, pure so it is unit-testable without a live
    connection. Postgres prefers the ``"lateral"`` backend
    (``optimizer/lateral_fetch.py`` - O(parents x page) instead of the
    window's O(all children), with an in-object windowed fallback for every
    shape the lateral SQL cannot express); every other vendor windows.
    """
    return {"postgresql": "lateral"}.get(vendor, "windowed")


def resolve_strategy(value: Any) -> NestedConnectionStrategy:
    """Resolve a strategy selection to an instance, failing loud on typos.

    Accepts a registered name (``"windowed"``), ``"auto"`` (eager vendor
    sniff of the default DB alias - construction-time so the instance-bound
    plan cache can never mix strategies), or a ``NestedConnectionStrategy``
    instance (a consumer-authored backend). ``None`` reads the
    ``NESTED_CONNECTION_STRATEGY`` setting, defaulting to ``"windowed"``.
    """
    if value is None:
        from ..conf import nested_connection_strategy_setting

        value = nested_connection_strategy_setting()
    if isinstance(value, str):
        if value == "auto":
            from django.db import connections
            from django.db.utils import DEFAULT_DB_ALIAS

            value = _strategy_for_vendor(connections[DEFAULT_DB_ALIAS].vendor)
        registry = _builtin_strategies()
        strategy = registry.get(value)
        if strategy is None:
            raise ConfigurationError(
                f"Unknown nested_connection_strategy {value!r}; expected one of "
                f"{sorted(registry)} or 'auto' or a NestedConnectionStrategy instance.",
            )
        return strategy
    if callable(getattr(value, "plan", None)):
        return value
    raise ConfigurationError(
        f"nested_connection_strategy must be a strategy name, 'auto', or an object "
        f"with a plan(request, plan) method; got {type(value).__name__}.",
    )


#: The active extension instance's strategy, published by
#: ``DjangoOptimizerExtension.on_execute`` for the walker (which cannot
#: import the extension module - the dependency points the other way).
_active_strategy: ContextVar[NestedConnectionStrategy | None] = ContextVar(
    "django_strawberry_framework_nested_fetch_strategy",
    default=None,
)


def active_strategy() -> NestedConnectionStrategy:
    """The strategy the current execution planned with; windowed by default."""
    return _active_strategy.get() or WINDOWED_STRATEGY
