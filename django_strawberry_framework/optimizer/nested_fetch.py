"""Pluggable nested-connection fetch strategies (the Prisma-style seam).

How a recognized nested Relay connection is FETCHED is a strategy, not the
optimizer's identity (the lesson from Prisma's ``JoinSelectBuilder`` trait:
one stable plan interface, swappable SQL shapes behind it). The private
planner (``optimizer/nested_planner.py::plan_connection_relation``) owns
everything strategy-independent - recognition, the Decision-6 fallback shapes
(sidecar, ``OptimizerHint.SKIP``, DISTINCT, malformed slice, unwindowable
partition), the divergent-alias per-response-key scheme (one request per key
under a per-key ``to_attr``), child-queryset construction, the deterministic
order, and the slice window - then hands each ``NestedConnectionRequest`` to
the active strategy, which attaches its fetch directives to an isolated
candidate plan. The candidate is merged only when the strategy returns
``True``; refusal and exceptions cannot mutate the planner result.

The default strategy is ``WindowedPrefetchStrategy`` - the verbatim spec-033
windowed prefetch: ``apply_window_pagination`` over the child queryset,
carried as a ``Prefetch(..., to_attr="_dst_<field>_connection")``. Any
strategy that lands an ordered list of model instances carrying
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
plans from two strategies. ``"auto"`` resolves to one stable auto strategy
whose plan is a lateral-capable WINDOWED queryset: the queryset's effective
DB alias selects lateral SQL only at fetch time, while every non-Postgres
alias executes the already-windowed ORM body. This keeps cached plans
backend-neutral and follows explicit ``.using(...)`` and router decisions
without consulting the default alias. The walker reaches the active
instance's strategy through a ``ContextVar`` the extension publishes in
``on_execute`` - direct ``plan_optimizations`` callers (tests) get the
windowed default.

Nested connection indexing
--------------------------
Both the windowed and lateral strategies partition each parent's children by
the child connector column and order them by the deterministic connection order,
so the database serves each page fastest from a composite index whose leading
columns mirror ``(parent_fk, order columns..., pk)``. For a keyset connection
the composite mirrors ``keyset.py::keyset_seek_q``'s redundant-leading-bound
design (the same leading columns the seek predicate compares). The planner emits
a dev-mode advisory (``optimizer/nested_planner.py::_advise_composite_index``,
``WARNING`` only under ``settings.DEBUG``) when no such index is found; it is
advisory only - DBAs own index creation, and expression indexes never trigger a
false positive. A per-field override
(``OptimizerHint.strategy("windowed" | "lateral" | "auto")`` in
``Meta.optimizer_hints``) selects which strategy fetches one connection field;
it is schema-static and needs no plan-cache-key change.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from contextvars import ContextVar
from dataclasses import dataclass
from functools import cache
from types import MappingProxyType
from typing import Any, Protocol

from django.db.models import Prefetch
from django.db.models.query import ModelIterable

from ..exceptions import ConfigurationError
from ..utils.connections import assert_window_fetch_mode_for
from .join_taxonomy import RelationJoinDescriptor
from .plans import OptimizationPlan, append_prefetch_unique, apply_window_pagination


def unwindowable_child_queryset_reason(queryset: Any) -> str | None:
    """Classify child-queryset states NO fetch strategy can window safely.

    The strategy-independent safety gate the nested planner runs before building a
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
    out: ``django_field`` is the RAW Django relation field/rel (the planner's
    ``_raw_relation_field``, not a ``FieldMeta`` - strategies may need
    ``remote_field`` / through metadata only the raw descriptor carries),
    ``child_queryset`` already carries the child plan (``only`` /
    ``select_related`` / nested prefetches / visibility hook), ``join`` is
    the relation's ``classify_relation_join`` descriptor (``windowable`` is
    ``True`` by construction here), ``order_by`` is the deterministic total
    order shared with resolve time, and ``(offset, limit, reverse,
    with_total_count)`` is the slice window. ``next_page_probe`` is the
    count-free ``hasNextPage`` overfetch flag (the n+1 probe): when set, the
    renderer fetches one sentinel row past the page (via the shared
    ``WindowRangePlan.fetch_*`` bounds) instead of the partition count; it is
    only ever ``True`` alongside ``with_total_count=False``. ``to_attr`` /
    ``lookup`` are the attach contract: the strategy's rows must land under
    ``to_attr`` on each parent reached via ``lookup``.
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
    next_page_probe: bool = False
    # The decoded ``cursor_field`` value seek (a ``keyset.KeysetSeek``) for a
    # keyset connection resolving ``after:``, or ``None`` (offset windows AND
    # keyset first pages alike). Forward-only by the walker's fallback
    # discipline; ``apply_window_pagination`` enforces that loudly.
    keyset_seek: Any | None = None

    def __post_init__(self) -> None:
        """Enforce the probe/count mutual-exclusion at the strategy seam.

        The request is the boundary EVERY strategy consumes, so validating the
        fetch mode here (the shared ``assert_window_fetch_mode_for``) guards the
        windowed and lateral backends alike against an engaged-probe window that
        also carries the partition count.
        """
        assert_window_fetch_mode_for(
            offset=self.offset,
            limit=self.limit,
            reverse=self.reverse,
            with_total_count=self.with_total_count,
            next_page_probe=self.next_page_probe,
        )


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


#: The single public strategy-selection type. Every seam that lets a consumer
#: choose a nested-connection fetch backend accepts this shape: the
#: ``DjangoOptimizerExtension`` constructor's ``nested_connection_strategy=``
#: kwarg, the ``OptimizerHint.nested_strategy`` field, and the
#: ``OptimizerHint.strategy(...)`` factory. A value is either a registered
#: strategy name (``"windowed"`` / ``"lateral"`` / ``"auto"``) or a
#: consumer-authored ``NestedConnectionStrategy`` instance; ``resolve_strategy``
#: validates it. Owned here beside ``NestedConnectionStrategy`` and
#: ``resolve_strategy`` so the three annotation sites share one definition; the
#: hint module imports it (and ``resolve_strategy``) at RUNTIME - the verified
#: import graph has no cycle (``nested_fetch`` never imports ``hints``), so the
#: annotation resolves under ``typing.get_type_hints`` without a custom
#: namespace.
StrategySelection = str | NestedConnectionStrategy


def attach_windowed_prefetch(
    request: NestedConnectionRequest,
    plan: OptimizationPlan,
    *,
    wrap: Callable[[Any], Any] | None = None,
) -> bool:
    """Window the request's child queryset and carry it as a ``to_attr`` Prefetch.

    The correctness FLOOR every strategy shares: ``apply_window_pagination``
    over ``request.child_queryset`` (spec-033's windowed prefetch, verbatim),
    attached under ``request.lookup`` / ``request.to_attr``. The windowed
    strategy calls it bare; the lateral strategy passes ``wrap`` to rebind the
    windowed queryset as its ``LateralQuerySet`` (same ORM body, lateral spec
    alongside). A future strategy (e.g. a portable correlated-subquery
    backend) inherits the floor - and any new window parameter - by calling
    this instead of copying the argument threading.

    Always returns ``True`` (the strategy-protocol "planned" verdict) so
    strategy ``plan`` bodies can end with ``return attach_windowed_prefetch(...)``.
    """
    windowed_queryset = apply_window_pagination(
        request.child_queryset,
        partition_by=request.join.partition_expr,
        order_by=request.order_by,
        offset=request.offset,
        limit=request.limit,
        reverse=request.reverse,
        with_total_count=request.with_total_count,
        next_page_probe=request.next_page_probe,
        keyset_seek=request.keyset_seek,
    )
    if wrap is not None:
        windowed_queryset = wrap(windowed_queryset)
    append_prefetch_unique(
        plan.prefetch_related,
        Prefetch(
            request.lookup,
            queryset=windowed_queryset,
            to_attr=request.to_attr,
        ),
    )
    return True


class WindowedPrefetchStrategy:
    """The default: spec-033's windowed prefetch, moved verbatim from the walker.

    The planned body is unchanged, but for the single-parent degenerate shape the
    windowed queryset is wrapped as a ``SingleParentWindowQuerySet`` (see
    ``optimizer/single_parent_fetch.py``): a RUNTIME-ONLY fast path that, when the
    Django-prefetch-injected parent ``IN`` list has length one, runs the plain
    filtered ``LIMIT`` query instead of the whole-partition ``ROW_NUMBER()``
    window and synthesizes ``_dst_row_number`` in Python. The wrap is plan-time
    (so it rides the plan cache), but the len==1 decision is fetch-time, and every
    unrecognized shape falls back to the identical windowed body - a performance
    downgrade, never a correctness cliff. Under the ``"lateral"``/``"auto"``
    strategies ``LateralPrefetchStrategy`` handles the clean eligible shape at
    plan time, so this fast path is effectively a ``"windowed"``-strategy feature;
    a lateral single-parent variant is out of v1 scope.
    """

    name = "windowed"

    def plan(self, request: NestedConnectionRequest, plan: OptimizationPlan) -> bool:
        """Window the child queryset and carry it as a ``to_attr`` Prefetch."""
        # Lazy import: single_parent_fetch imports lateral_fetch which imports
        # this module (the same cycle the auto strategy breaks lazily).
        from .single_parent_fetch import as_single_parent_queryset, single_parent_spec

        spec = single_parent_spec(request)
        if spec is None:
            return attach_windowed_prefetch(request, plan)
        return attach_windowed_prefetch(
            request,
            plan,
            wrap=lambda queryset: as_single_parent_queryset(queryset, spec),
        )


#: The shared default-strategy singleton (stateless, so one instance serves
#: every extension and every direct ``plan_optimizations`` caller).
WINDOWED_STRATEGY = WindowedPrefetchStrategy()


class AutoNestedConnectionStrategy:
    """Plan a backend-neutral queryset that chooses by its fetch-time DB alias.

    The lateral backend always carries the complete windowed ORM query as its
    superclass fallback. Delegating every auto plan to that backend therefore
    gives Postgres the lateral fast path while every other vendor executes the
    same bounded window the explicit ``"windowed"`` strategy would have built.
    The strategy object itself never changes, so an extension's cached plans
    cannot mix backend-specific planning modes.
    """

    name = "auto"

    def plan(self, request: NestedConnectionRequest, plan: OptimizationPlan) -> bool:
        """Attach a fetch-time vendor-aware, lateral-capable windowed prefetch."""
        # Lazy to break the intentional cycle: lateral_fetch imports this
        # module's request and window-floor primitives.
        from .lateral_fetch import LATERAL_STRATEGY

        return LATERAL_STRATEGY.plan(request, plan)


#: The shared automatic-strategy singleton. It remains stable across every DB
#: route; ``LateralQuerySet._fetch_all`` selects by the queryset's actual alias.
AUTO_STRATEGY = AutoNestedConnectionStrategy()


@cache
def _builtin_strategies() -> Mapping[str, NestedConnectionStrategy]:
    """Build the immutable built-in registry after breaking the import cycle."""
    from .lateral_fetch import LATERAL_STRATEGY

    return MappingProxyType({"windowed": WINDOWED_STRATEGY, "lateral": LATERAL_STRATEGY})


def resolve_strategy(value: Any) -> NestedConnectionStrategy:
    """Resolve a strategy selection to an instance, failing loud on typos.

    Accepts a registered name (``"windowed"`` / ``"lateral"``), ``"auto"``
    (one stable strategy whose lateral-capable queryset chooses from its
    fetch-time DB alias), or a ``NestedConnectionStrategy`` instance (a
    consumer-authored backend). ``None`` reads the
    ``NESTED_CONNECTION_STRATEGY`` setting, defaulting to ``"windowed"``.
    """
    if value is None:
        from ..conf import nested_connection_strategy_setting

        value = nested_connection_strategy_setting()
    if isinstance(value, str):
        if value == "auto":
            return AUTO_STRATEGY
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
