"""``OptimizationPlan`` - the shape the walker emits and the extension consumes.

The plan is a simple data class carrying optimization directives and metadata:

- ``select_related``: forward FK / OneToOne joins that collapse into the
  parent query via ``QuerySet.select_related(*names)``.
- ``prefetch_related``: many-side relations (reverse FK, M2M) and
  visibility-downgraded forward rels, usually expressed as
  ``django.db.models.Prefetch`` objects. Consumed by
  ``QuerySet.prefetch_related(*lookups)``.
- ``only_fields``: scalar column names for ``QuerySet.only(*names)``,
  including the FK columns required to materialize ``select_related``
  joins so Django doesn't mark them as deferred and re-query.
- ``fk_id_elisions``: branch-sensitive resolver keys for forward FK /
  OneToOne fields where only the target primary key is selected, so the
  resolver can use the source row's ``<field>_id`` value instead of
  lazy-loading the related row.
- ``planned_resolver_keys``: branch-sensitive resolver keys for relations
  covered by the plan, used by strictness checks.
- ``finalized_*`` metadata: immutable membership sets computed during
  ``finalize()`` so context publishing can reuse cache-hit metadata without
  rebuilding sets or lookup paths.
- ``cacheable``: whether this plan can be reused from the extension's plan
  cache.

The plan starts with mutable sequence fields while the walker descends the
selection tree, then ``finalize()`` publishes tuple-backed fields for cache and
extension handoff. The extension applies the final plan to the root queryset
in a single pass once the walk completes.
"""

from __future__ import annotations

import contextlib
import sys
from collections.abc import Iterable, MutableSequence, Sequence
from dataclasses import dataclass, field, replace
from typing import Any

from django.core.exceptions import FieldDoesNotExist
from django.db.models import Count, Prefetch, Window
from django.db.models.functions import RowNumber

from ..exceptions import OptimizerError
from ..utils.relations import relation_kind


def _identity(value: Any) -> Any:
    """Return ``value`` for default index keys."""
    return value


def _lookup_path(entry: Any) -> str:
    """Return the prefetch lookup path for an entry (string or ``Prefetch``).

    Centralizes the brittle Django-private contract for ``Prefetch.prefetch_to``
    so a future Django rename has one fix.  Plain-string entries are
    returned as-is (they double as their own path).
    """
    return getattr(entry, "prefetch_to", entry)


class _IndexedList(list[Any]):
    """List with a construction-time membership index for optimizer builders.

    Only ``append``, ``extend``, and ``append_unique`` maintain the ``_seen``
    sidecar index. The other ``list`` mutators (``insert``, ``remove``,
    ``pop``, slice assignment, and in-place ``+=``, which CPython routes
    through ``list.__iadd__`` rather than the overridden ``extend``) would
    desynchronize the index from the contents. Every optimizer writer goes
    through the three maintained entry points, so this is a usage constraint,
    not a runtime guard: a future caller reaching for any other mutator must
    rebuild the list instead.
    """

    __slots__ = ("_key", "_seen")

    def __init__(self, values: Iterable[Any] = (), *, key: Any = _identity) -> None:
        super().__init__()
        self._key = key
        self._seen: set[Any] = set()
        for value in values:
            self.append_unique(value)

    def append_unique(self, value: Any) -> None:
        """Append ``value`` once, using the sidecar index when the key is hashable."""
        index_key = self._key(value)
        try:
            if index_key in self._seen:
                return
        except TypeError:
            if value in self:
                return
        super().append(value)
        with contextlib.suppress(TypeError):
            self._seen.add(index_key)

    def append(self, value: Any) -> None:
        """Append directly and keep the sidecar index useful for later helper calls."""
        super().append(value)
        with contextlib.suppress(TypeError):
            self._seen.add(self._key(value))

    def extend(self, values: Iterable[Any]) -> None:
        """Extend directly and keep the sidecar index useful for later helper calls."""
        for value in values:
            self.append(value)


def _indexed_list() -> _IndexedList:
    """Return an indexed list for string-like optimizer directive fields."""
    return _IndexedList()


def _prefetch_indexed_list() -> _IndexedList:
    """Return an indexed list keyed by Django prefetch lookup path."""
    return _IndexedList(key=_lookup_path)


@dataclass
class OptimizationPlan:
    """Immutable-ish bag of optimizer directives for one root queryset.

    Constructed by ``plan_optimizations`` in ``optimizer/walker.py`` and
    consumed by ``DjangoOptimizerExtension`` in ``optimizer/extension.py``.

    Cache invariant: once a plan has been handed off (returned from the
    walker, stashed on ``info.context``, or stored in the extension's
    plan cache), it must not be mutated in place.  Use
    ``dataclasses.replace`` to derive a modified plan.  The stored fields
    are typed as ``Sequence`` because they are lists during construction
    and tuples after ``finalize()``; mutator helpers retain
    ``MutableSequence`` parameters for the walker-only construction path.

    Scope of the post-``finalize()`` immutability enforcement: the
    five directive fields (``select_related``, ``prefetch_related``,
    ``only_fields``, ``fk_id_elisions``, ``planned_resolver_keys``) are
    swapped to tuples, so ``plan.prefetch_related.append(...)`` after
    handoff raises ``AttributeError``; the three ``finalized_*`` metadata fields
    are swapped to frozensets. The ``cacheable`` bool remains a plain settable
    attribute and its post-handoff immutability is a convention enforced by the
    single writer ``walker.py::plan_optimizations`` (pre-finalize only).
    Trigger to move ``OptimizationPlan`` to ``@dataclass(frozen=True)``: a
    second writer that flips ``cacheable`` lands, or a cache-poisoning incident
    surfaces a post-finalize mutation.
    """

    select_related: Sequence[str] = field(default_factory=_indexed_list)
    """Forward FK / OneToOne field names for ``QuerySet.select_related``."""

    prefetch_related: Sequence[str | Prefetch] = field(default_factory=_prefetch_indexed_list)
    """Strings or ``Prefetch`` objects for ``QuerySet.prefetch_related``.

    Generated relation plans use ``Prefetch`` objects so child querysets can
    consistently carry projection and nested lookup state. Plain strings are
    still accepted for compatibility with manual plans or defensive fallback
    branches.
    """

    only_fields: Sequence[str] = field(default_factory=_indexed_list)
    """Scalar column names for ``QuerySet.only``."""
    fk_id_elisions: Sequence[str] = field(default_factory=_indexed_list)
    """Resolver keys elided because the source row already carries the target id."""
    planned_resolver_keys: Sequence[str] = field(default_factory=_indexed_list)
    """Resolver keys for relations covered by this plan, used by B3 strictness."""
    finalized_fk_id_elisions: frozenset[str] | None = None
    """Frozen membership set for ``fk_id_elisions`` after ``finalize()``."""
    finalized_planned_resolver_keys: frozenset[str] | None = None
    """Frozen membership set for ``planned_resolver_keys`` after ``finalize()``."""
    finalized_lookup_paths: frozenset[str] | None = None
    """Frozen Django lookup paths covered by this plan after ``finalize()``."""
    cacheable: bool = True
    """Whether this plan can be reused from the extension's plan cache.

    O6 ``Prefetch`` downgrades may embed querysets produced by
    ``DjangoType.get_queryset(queryset, info)``. Those querysets can be
    request-dependent because ``info.context`` may carry the current
    user, tenant, or permissions. Plans containing such dynamic
    querysets must be applied for the current request only.
    """

    @property
    def is_empty(self) -> bool:
        """Return ``True`` when no optimization directives were collected.

        ``cacheable`` is metadata about cache reuse and is excluded from the
        emptiness check.  Consequence: an ``OptimizationPlan(cacheable=False)``
        with no other directives reports ``is_empty=True`` (pinned by
        ``tests/optimizer/test_plans.py::test_cacheable_flag_does_not_affect_empty_state``),
        so a resolver keying off ``is_empty`` for a "skip optimizer"
        early-out will not see the uncacheable-flag signal.  Trigger to
        revisit: a resolver-side call site reads ``is_empty`` and
        ``cacheable`` together for a logic decision.  Today only
        ``apply()`` is empty-tolerant and the extension's
        ``plan_relation`` / ``_optimize`` paths do not branch on
        ``is_empty``.
        """
        return (
            not self.select_related
            and not self.prefetch_related
            and not self.only_fields
            and not self.fk_id_elisions
            and not self.planned_resolver_keys
        )

    def finalize(self) -> OptimizationPlan:
        """Swap mutable list fields for tuples so post-handoff mutation raises.

        Called once at walker exit (``plan_optimizations`` return) and at
        every ``dataclasses.replace`` site that publishes a derived plan
        (e.g. ``diff_plan_for_queryset``). Enforces the documented
        "immutable-after-handoff" cache invariant: appending to the
        cached plan's ``prefetch_related`` after finalisation raises
        ``AttributeError`` instead of silently poisoning the plan cache
        for subsequent requests.

        Idempotent: re-finalising a plan that already carries tuples
        leaves it unchanged. Use ``dataclasses.replace`` to derive a
        modified plan from a finalised one (the walker still owns the
        construction-time mutation path).
        """
        select_related = tuple(self.select_related)
        prefetch_related = tuple(self.prefetch_related)
        return replace(
            self,
            select_related=select_related,
            prefetch_related=prefetch_related,
            only_fields=tuple(self.only_fields),
            fk_id_elisions=tuple(self.fk_id_elisions),
            planned_resolver_keys=tuple(self.planned_resolver_keys),
            finalized_fk_id_elisions=frozenset(self.fk_id_elisions),
            finalized_planned_resolver_keys=frozenset(self.planned_resolver_keys),
            finalized_lookup_paths=frozenset(
                _lookup_paths_from_parts(select_related, prefetch_related),
            ),
        )

    def apply(self, queryset: Any) -> Any:
        """Apply the plan to a ``QuerySet`` and return the optimized copy.

        Applies in order: ``only()`` -> ``select_related()`` ->
        ``prefetch_related()``. The order matters because
        ``select_related`` may narrow ``only()`` column lists and
        ``prefetch_related`` may carry nested ``Prefetch`` objects whose
        inner querysets already have their own ``only()`` applied.
        """
        if self.only_fields:
            queryset = queryset.only(*self.only_fields)
        if self.select_related:
            queryset = queryset.select_related(*self.select_related)
        if self.prefetch_related:
            queryset = queryset.prefetch_related(*self.prefetch_related)
        return queryset


def resolver_key(parent_type: type | None, field_name: str, runtime_path: tuple[str, ...]) -> str:
    """Return the branch-sensitive resolver key shared by walker and resolvers."""
    path = ".".join(runtime_path)
    if parent_type is None:
        return f"{field_name}@{path}"
    return f"{parent_type.__name__}.{field_name}@{path}"


def runtime_path_from_info(info: Any | None) -> tuple[str, ...]:
    """Return the runtime path tuple from a GraphQL ``info`` (or ``()`` when absent).

    Thin wrapper that pulls ``info.path`` and delegates to
    ``runtime_path_from_path``; ``info=None`` short-circuits to the
    empty tuple so resolver-key construction stays branch-free at the
    call site.
    """
    if info is None:
        return ()
    return runtime_path_from_path(getattr(info, "path", None))


# A GraphQL ``path`` linked-list is exactly the *static* selection-set nesting of
# the query document (result-set size and data-tree depth do NOT deepen it - list
# items are sibling paths at depth+1, not nested levels). graphql-core's executor
# also recurses one Python frame per level, so a query deep enough to approach
# this would hit Python's recursion limit first. This ceiling therefore sits far
# above any real query; exceeding it means the ``prev`` chain is cyclic or corrupt.
# The cap's only job is to catch such a cycle, which terminates in N iterations
# regardless of N - so it is set generously (1024) to make a false positive on a
# legitimate query effectively impossible while still turning a would-be infinite
# hang into a loud failure with a fixed, statically-checkable upper bound (NASA
# Power-of-Ten Rule 2).
_MAX_PATH_DEPTH = 1024


def runtime_path_from_path(path: Any) -> tuple[str, ...]:
    """Walk a GraphQL ``path`` linked-list and return its keys, list indexes stripped.

    Iterates ``path.prev`` from the deepest selection back to the root,
    skipping integer keys (graphql-core's list-index entries) so the
    resulting tuple is a stable structural identity for cache-key and
    resolver-key purposes.

    The walk is bounded by ``_MAX_PATH_DEPTH`` rather than looping
    unconditionally: a ``prev`` chain is exactly the resolver nesting depth,
    which graphql-core bounds by the validated query depth, so a chain longer
    than that ceiling can only be cyclic or corrupt and raises ``RuntimeError``
    instead of spinning forever.
    """
    keys: list[str] = []
    node = path
    for _ in range(_MAX_PATH_DEPTH):
        if node is None:
            return tuple(reversed(keys))
        key = getattr(node, "key", None)
        if not isinstance(key, int) and key is not None:
            keys.append(str(key))
        node = getattr(node, "prev", None)
    raise RuntimeError(
        f"runtime_path_from_path: GraphQL path exceeded {_MAX_PATH_DEPTH} levels; "
        "the `prev` chain is likely cyclic or corrupt.",
    )


def _flatten_select_related(sr: Any) -> set[str]:
    """Flatten Django's ``query.select_related`` into a set of dotted paths.

    Django stores ``select_related`` in three shapes:

    - ``False`` (the default - nothing has been selected): empty set.
    - ``True`` (the wildcard ``select_related()`` form): empty set as
      well. Django's wildcard only follows non-null FKs, so we cannot
      treat it as covering every optimizer entry - nullable FKs in the
      plan still need to be applied. Treating ``True`` as no overlap
      keeps optimizer entries; the consumer's wildcard will be narrowed
      by Django's subsequent ``select_related(*names)`` call, a known
      interaction that consumers combining wildcard ``select_related()``
      with this optimizer should be aware of.
    - ``dict`` (a nested mapping of selected field names): flattens to
      dotted lookup paths via recursive walk, e.g.
      ``{"category": {"parent": {}}}`` -> ``{"category", "category__parent"}``.
    """
    if sr is False or sr is True:
        return set()
    paths: set[str] = set()

    def _walk(d: dict[str, Any], prefix: str) -> None:
        for key, child in d.items():
            path = f"{prefix}__{key}" if prefix else key
            paths.add(path)
            if isinstance(child, dict) and child:
                _walk(child, path)

    _walk(sr, "")
    return paths


def append_unique(values: MutableSequence[Any], value: Any) -> None:
    """Append ``value`` to ``values`` if it is not already present.

    Plan-shape mutator: lives next to ``OptimizationPlan`` so the dedupe
    discipline is a property of the plan list shape rather than a
    walker-local convention.
    """
    if isinstance(values, _IndexedList):
        values.append_unique(value)
        return
    if value not in values:
        values.append(value)


def append_unique_many(values: MutableSequence[Any], new_values: Iterable[Any]) -> None:
    """Append each value in ``new_values`` if it is not already present."""
    for value in new_values:
        append_unique(values, value)


def append_prefetch_unique(values: MutableSequence[Any], prefetch: Prefetch) -> None:
    """Append ``prefetch`` unless a lookup for the same path already exists.

    Compares lookup paths via ``_lookup_path`` so a hint-supplied
    ``Prefetch(obj)`` and a walker-generated ``Prefetch`` for the same
    Django lookup are recognised as duplicates regardless of queryset
    identity. Generated duplicate selections are merged before child
    querysets are built; this helper remains the first-seen path dedupe
    for already-built ``Prefetch`` entries.
    """
    if isinstance(values, _IndexedList):
        values.append_unique(prefetch)
        return
    lookup_path = _lookup_path(prefetch)
    if any(_lookup_path(value) == lookup_path for value in values):
        return
    values.append(prefetch)


def _consumer_prefetch_lookups(queryset: Any) -> list[Any]:
    """Return the ``_prefetch_related_lookups`` already attached to a queryset.

    Centralizes the brittle Django-private contract for
    ``QuerySet._prefetch_related_lookups``.  Returns an empty list when
    the queryset has no prefetches (or the attribute is missing entirely
    on a non-QuerySet input).  The trailing ``or ()`` is a paranoid
    guard for non-``QuerySet`` inputs (test doubles, custom managers)
    whose ``_prefetch_related_lookups`` attribute is present but
    ``None``; stock Django always stores a tuple
    (``prefetch_related(None)`` resets to ``()``), so the guard is dead
    code under a real ``QuerySet``.  Trigger to revisit removal: a real
    consumer surfaces a ``None`` lookups attribute or the test-double
    case is otherwise retired.
    """
    return list(getattr(queryset, "_prefetch_related_lookups", ()) or ())


def _consumer_only_fields(queryset: Any) -> frozenset[str] | None:
    """Return the consumer-applied ``.only()`` field set, or ``None``.

    Centralizes the brittle Django-private contract for
    ``QuerySet.query.deferred_loading``, a ``(field_set, defer_flag)``
    tuple where ``defer_flag is False`` means ``.only()`` was applied
    (Django's "load only this set" mode) and ``defer_flag is True`` is
    the default ``.defer()``-or-nothing mode.

    Returns the non-empty only-set when the consumer applied ``.only()``;
    returns ``None`` otherwise (no ``.only()`` applied, ``.defer()`` mode,
    or the attribute is missing on a non-QuerySet input). The wildcard
    ``.only()`` with no args is not a meaningful consumer projection
    (Django collapses it to the default empty set in defer mode) and is
    handled implicitly by the non-empty check.
    """
    query = getattr(queryset, "query", None)
    deferred_loading = getattr(query, "deferred_loading", None)
    if deferred_loading is None:
        return None
    try:
        field_set, defer_flag = deferred_loading
    except (TypeError, ValueError):
        return None
    if defer_flag is not False:
        return None
    if not field_set:
        return None
    return frozenset(field_set)


def _optimizer_can_absorb(
    opt_entry: Any,
    consumer_paths: Sequence[str],
    consumer_by_path: dict[str, Any],
) -> bool:
    """Return ``True`` when ``opt_entry`` can losslessly take over the consumer's subtree.

    All three conditions must hold:

    1. The optimizer entry is a ``Prefetch`` carrying a queryset (a
       bare string carries no projection / nested chain that would
       justify replacing the consumer's entries).
    2. Every matching consumer entry is a bare string. A consumer
       ``Prefetch`` with a custom queryset cannot be losslessly
       replaced.
    3. Every matching consumer path is covered by the optimizer's own
       lookup tree. Otherwise the consumer has prefetches the
       optimizer would not replace, and absorbing them would silently
       drop data - for example, optimizer
       ``Prefetch("items", queryset=Item.objects.only("name"))``
       cannot absorb consumer ``"items__entries"``.
    """
    if getattr(opt_entry, "queryset", None) is None:
        return False
    if not all(isinstance(consumer_by_path[p], str) for p in consumer_paths):
        return False
    opt_covered = _prefetch_lookup_paths([opt_entry])
    return all(path in opt_covered for path in consumer_paths)


# Package-reserved annotation names for the windowed-prefetch mechanism. The
# ``_dst_*`` namespace (NOT upstream's ``_strawberry_*``) keeps a consumer running
# both django-strawberry-framework and strawberry-graphql-django in one process
# from colliding (spec-033 "Explicitly do not borrow"). ``_dst_row_number`` /
# ``_dst_total_count`` are read by the connection-class fast path in Slice 2.
WINDOW_ROW_NUMBER = "_dst_row_number"
WINDOW_TOTAL_COUNT = "_dst_total_count"
WINDOW_ROW_NUMBER_REVERSED = "_dst_row_number_reversed"


def ends_in_unique_column(effective: tuple, model: type) -> bool:
    """Return whether the effective ordering's terminal entry is a unique total order.

    Hoisted from ``connection.py`` (spec-033 Decision 11) so the plan-time
    window order and the resolve-time pipeline order share ONE implementation -
    the cursor-parity invariant: window row numbers must agree with the
    fallback path's offset cursors. ``connection.py`` imports this back.

    A connection's positional offset cursors are only stable across separate
    requests when the SQL ``ORDER BY`` is a deterministic TOTAL order. An
    ordering whose terminal column is unique (the pk, or a ``unique=True`` model
    field) already is one; otherwise ``deterministic_order`` appends the pk as a
    terminal tiebreaker.

    Handles both string order refs (``"name"``, ``"-name"``, ``"shelf__code"``,
    ``"pk"``) and ``OrderBy`` / ``F`` expressions (the NULLS-positioning and the
    to-many-aggregate paths). A relation path, an aggregate-annotation alias, or
    any non-``F`` expression is treated as non-unique (so the pk is appended).
    """
    if not effective:
        return False
    terminal = effective[-1]
    if isinstance(terminal, str):
        ref: str | None = terminal.lstrip("-")
    else:
        ref = getattr(getattr(terminal, "expression", None), "name", None)
    if not ref:
        return False
    pk = model._meta.pk
    if ref in ("pk", pk.name, pk.attname):
        return True
    if "__" in ref:
        # A relation traversal (e.g. ``shelf__code``) is not the model's own
        # unique column; the related column's uniqueness does not make the
        # parent ordering a total order.
        return False
    try:
        field_obj = model._meta.get_field(ref)
    except FieldDoesNotExist:
        # Annotation alias (e.g. a to-many aggregate) or a transform - not a
        # model column we can call unique.
        return False
    return bool(getattr(field_obj, "unique", False) or getattr(field_obj, "primary_key", False))


def deterministic_order(effective: tuple, model: type) -> tuple:
    """Return the deterministic TOTAL ordering tuple for a connection queryset.

    The effective ordering with the model pk appended as a terminal tiebreaker
    UNLESS it already ends in a unique column (``ends_in_unique_column``). One
    source for both the plan-time window ``order_by`` (the walker's
    ``_plan_connection_relation``) and the resolve-time pipeline
    (``connection.py::_finalize_queryset``) so window row numbers can never drift
    from fallback-path cursors (spec-033 Decision 11, the cursor-parity
    invariant).
    """
    if ends_in_unique_column(effective, model):
        return effective
    return (*effective, model._meta.pk.attname)


def window_partition_for_prefetch(field: Any) -> str:
    """Return the parent-side partition expression for a windowed prefetch.

    The expression Django's prefetch attach uses to map each child row back to
    its parent - ``remote_field.attname or remote_field.name`` on the relation
    field, exactly what upstream's ``_optimize_prefetch_queryset`` partitions by
    (spec-033 Decision 4). By relation kind (the ``_ensure_connector_only_fields``
    dispatch structure, but the PARENT-side partition, not the child ``.only()``
    connector):

    - reverse FK / reverse one-to-one -> the child-table FK attname
      (``"shelf_id"`` / ``"patron_id"``);
    - reverse M2M -> the child's forward M2M field name (``Genre.books`` ->
      ``"genres"``);
    - forward M2M -> the target's reverse query name, which is NOT the accessor
      when ``related_name`` is absent (``Book.genres`` -> ``"books"``).

    Takes the RAW Django relation field (not a ``FieldMeta``): the forward-M2M
    reverse query name lives only on ``field.remote_field`` and is not carried on
    ``FieldMeta``. Raises ``OptimizerError`` for a single-valued forward relation
    or any kind without a windowable partition, so ``_plan_connection_relation``
    leaves the selection unplanned and falls back per-parent rather than guessing.
    """
    kind = relation_kind(field)
    if kind not in ("many", "reverse_many_to_one", "reverse_one_to_one"):
        raise OptimizerError(
            f"window_partition_for_prefetch: relation {getattr(field, 'name', field)!r} "
            f"has kind {kind!r}, which has no windowable parent partition; "
            "the nested connection falls back to per-parent resolution.",
        )
    remote_field = getattr(field, "remote_field", None)
    partition = getattr(remote_field, "attname", None) or getattr(remote_field, "name", None)
    if partition is None:
        raise OptimizerError(
            f"window_partition_for_prefetch: could not resolve a parent partition for "
            f"relation {getattr(field, 'name', field)!r}; falling back to per-parent.",
        )
    return partition


def apply_window_pagination(
    queryset: Any,
    *,
    partition_by: str,
    order_by: Sequence[Any],
    offset: int = 0,
    limit: int | None = None,
    reverse: bool = False,
) -> Any:
    """Annotate row-number / total-count windows and filter to the requested slice.

    The mechanism port of
    ``strawberry-django-main/strawberry_django/pagination.py::apply_window_pagination``
    (itself based on Django's https://github.com/django/django/pull/15957),
    namespaced ``_dst_*`` (spec-033 Decision 4). Diverges from upstream's
    signature by taking ``partition_by`` and ``order_by`` EXPLICITLY (rather than
    a ``related_field_id`` plus a compiler-derived order) so ``plans.py`` stays
    free of queryset-compiler coupling and the deterministic order comes from the
    shared ``deterministic_order`` helper (the cursor-parity invariant).

    Annotates ``_dst_row_number`` (``RowNumber()`` partitioned by ``partition_by``,
    ordered by ``order_by``) and ``_dst_total_count`` (``Count(1)`` partitioned the
    same way), then filters to the requested row-number range. The annotations
    compose with ``.only()`` (they are annotations, not deferred columns).

    The same ``order_by`` tuple is also applied to the queryset itself via
    ``.order_by(*order_by)``: the SQL window only determines the ROW-NUMBER
    VALUES, not the order Django hands the prefetched instances to ``to_attr``,
    and the connection fast path
    (``connection.py::_resolve_from_window``) consumes ``rows`` as
    already forward-ordered (``rows[0]`` / ``rows[-1]`` / edge iteration drive the
    cursors and ``pageInfo``). Sourcing the window order and the return order from
    one tuple by construction keeps the fast path from diverging from the
    fallback pipeline when the DB's natural return order is not the connection
    order (spec-033 Decision 11, the cursor-parity invariant). The forward order
    is applied in BOTH branches: the ``reverse`` (last-only) window keeps
    ``_dst_row_number`` forward, so its rows are forward-ordered too.

    ``offset`` / ``limit`` come from Strawberry's ``SliceMetadata.from_arguments``
    (offset = ``start``, limit = ``expected``). For ``reverse`` (last-only backward
    pagination) the row numbers count from the partition end, so a separate
    ``_dst_row_number_reversed`` window with the reversed order filters
    ``__lte=limit``. ``limit is None`` (or ``sys.maxsize``) means "no upper bound"
    - the offset filter still applies.
    """
    queryset = queryset.order_by(*order_by)
    queryset = queryset.annotate(
        **{
            WINDOW_ROW_NUMBER: Window(
                RowNumber(),
                partition_by=partition_by,
                order_by=order_by,
            ),
            WINDOW_TOTAL_COUNT: Window(Count(1), partition_by=partition_by),
        },
    )
    if offset:
        queryset = queryset.filter(**{f"{WINDOW_ROW_NUMBER}__gt": offset})
    if reverse:
        queryset = queryset.annotate(
            **{
                WINDOW_ROW_NUMBER_REVERSED: Window(
                    RowNumber(),
                    partition_by=partition_by,
                    order_by=_reverse_order_by(order_by),
                ),
            },
        )
        if limit is not None and limit != sys.maxsize:
            queryset = queryset.filter(**{f"{WINDOW_ROW_NUMBER_REVERSED}__lte": limit})
        return queryset
    # ``limit is None`` / ``sys.maxsize`` => no upper bound (relay's last-only
    # forward shape sets ``end = sys.maxsize``; the offset filter alone applies).
    if limit is not None and limit >= 0 and limit != sys.maxsize:
        queryset = queryset.filter(**{f"{WINDOW_ROW_NUMBER}__lte": offset + limit})
    return queryset


def _reverse_order_by(order_by: Sequence[Any]) -> list[Any]:
    """Return ``order_by`` with each entry's direction (and NULLS) flipped.

    Backward (``last``-only) pagination counts row numbers from the partition
    end, which needs the reversed ordering. Mirrors Django's
    ``queryset.reverse()`` for the string and ``OrderBy`` / expression shapes
    ``deterministic_order`` produces, without re-running the queryset compiler:
    the direction flips, and any explicit ``nulls_first`` / ``nulls_last``
    positioning swaps too (Django inverts NULLS placement on reversal), so a
    consumer ordering with explicit NULLS positioning reverses the same way the
    resolve-time ``.reverse()`` pipeline does.
    """
    reversed_order: list[Any] = []
    for entry in order_by:
        if isinstance(entry, str):
            reversed_order.append(entry[1:] if entry.startswith("-") else f"-{entry}")
        else:
            descending = getattr(entry, "descending", None)
            if descending is None:
                reversed_order.append(entry)
            else:
                clone = entry.copy() if hasattr(entry, "copy") else entry
                clone.descending = not descending
                nulls_first = getattr(clone, "nulls_first", None)
                nulls_last = getattr(clone, "nulls_last", None)
                if nulls_first or nulls_last:
                    clone.nulls_first, clone.nulls_last = nulls_last, nulls_first
                reversed_order.append(clone)
    return reversed_order


def diff_plan_for_queryset(plan: OptimizationPlan, queryset: Any) -> tuple[OptimizationPlan, Any]:
    """Reconcile ``plan`` against optimizations already on ``queryset``.

    Returns ``(delta_plan, queryset_to_apply_against)``. The plan is
    only ever copied (never mutated) so B1's cache stays intact. The
    queryset is rewritten only when the consumer applied a plain
    ``prefetch_related("path")`` string that the optimizer can replace
    with a more specific ``Prefetch(path, queryset=...)`` carrying
    nested chains or projection.

    Reconciliation rules:

    ``select_related`` - compared as dotted lookup paths against the
    consumer's existing ``query.select_related`` dict. Exact matches
    are dropped from the plan; the wildcard form (``True``) is treated
    as no overlap so explicit nullable-FK entries still apply.

    ``only_fields`` - dropped entirely when the consumer already
    applied ``.only(...)`` to the queryset (detected via
    ``query.deferred_loading`` with ``defer_flag is False`` and a
    non-empty field set). Django's ``QuerySet.only(...).only(...)``
    chaining *replaces* the previous deferred-field set rather than
    merging, so applying the optimizer's ``only_fields`` on top of a
    consumer ``.only()`` would silently drop the consumer's projection
    - including columns the consumer may have restricted to enforce a
    permission boundary. The conservative consumer-wins choice is to
    drop the optimizer's ``only_fields`` whenever the consumer has
    already restricted columns; ``.defer(...)`` is not treated as a
    consumer projection because ``.defer()`` and ``.only()`` compose
    cleanly in Django.

    ``prefetch_related`` - compared by ``prefetch_to`` with ancestry
    awareness. For each optimizer entry we gather the consumer entries
    on the same subtree (exact path or any descendant of it) and
    decide as a group:

    - **No consumer entries on the subtree** - the optimizer entry
      passes through unchanged.
    - **Optimizer can losslessly absorb the consumer subtree** - when
      the optimizer entry is a ``Prefetch`` carrying a queryset, every
      matching consumer entry is a bare string, *and* every matching
      consumer path is covered by the optimizer's own lookup tree
      (``_prefetch_lookup_paths``), the consumer strings are stripped
      from the queryset and the optimizer's nested ``Prefetch`` takes
      over. This is what makes
      ``prefetch_related("items", "items__entries")`` cooperate with
      ``Prefetch("items", queryset=...prefetch_related("entries"))``
      instead of raising ``ValueError: 'items' lookup was already seen
      with a different queryset``.
    - **Consumer wins** - for any other shape (consumer's own custom
      ``Prefetch`` somewhere on the subtree, plain-string-vs-
      plain-string match where the optimizer has no queryset, or a
      consumer descendant the optimizer's own subtree does not cover),
      the optimizer entry is dropped to avoid the collision and to
      avoid silently stripping consumer prefetches the optimizer would
      not replace.
    """
    new_select = _diff_select_related(plan.select_related, queryset)
    new_prefetch, new_queryset = _diff_prefetch_related(plan.prefetch_related, queryset)
    drop_only_fields = bool(plan.only_fields) and _consumer_only_fields(queryset) is not None
    new_only_fields: Sequence[str] = () if drop_only_fields else plan.only_fields

    if (
        len(new_select) == len(plan.select_related)
        and len(new_prefetch) == len(plan.prefetch_related)
        and new_queryset is queryset
        and not drop_only_fields
    ):
        return plan, queryset
    return (
        replace(
            plan,
            select_related=new_select,
            prefetch_related=new_prefetch,
            only_fields=new_only_fields,
        ).finalize(),
        new_queryset,
    )


def _diff_select_related(plan_select_related: Sequence[str], queryset: Any) -> list[str]:
    """Drop optimizer ``select_related`` entries that the queryset already has.

    Compared as dotted lookup paths against the consumer's existing
    ``query.select_related`` dict.  Exact matches are dropped; the
    wildcard form (``True``) is treated as no overlap so explicit
    nullable-FK entries still apply (see ``_flatten_select_related``).
    Defensive: a queryset-shaped object without ``.query`` is treated
    as having no existing select_related, matching the rest of the
    file's defensive ``getattr`` style.
    """
    query = getattr(queryset, "query", None)
    already_select = _flatten_select_related(getattr(query, "select_related", False))
    return [name for name in plan_select_related if name not in already_select]


def _diff_prefetch_related(
    plan_prefetch_related: Sequence[Any],
    queryset: Any,
) -> tuple[list[Any], Any]:
    """Reconcile optimizer ``prefetch_related`` against the queryset's existing lookups.

    Returns ``(new_prefetch_list, queryset_to_apply_against)``.  See
    ``diff_plan_for_queryset`` for the full reconciliation rules.
    """
    consumer_pf = _consumer_prefetch_lookups(queryset)
    consumer_by_path: dict[str, Any] = {_lookup_path(entry): entry for entry in consumer_pf}

    new_prefetch: list[Any] = []
    paths_to_strip: set[str] = set()

    for opt_entry in plan_prefetch_related:
        opt_path = _lookup_path(opt_entry)
        descendant_prefix = f"{opt_path}__"
        matching_paths = [
            path
            for path in consumer_by_path
            if path == opt_path or path.startswith(descendant_prefix)
        ]
        if not matching_paths:
            new_prefetch.append(opt_entry)
            continue
        if _optimizer_can_absorb(opt_entry, matching_paths, consumer_by_path):
            paths_to_strip.update(matching_paths)
            new_prefetch.append(opt_entry)
        # else: consumer wins on this subtree; optimizer dropped.

    new_queryset = queryset
    if paths_to_strip:
        keep = tuple(entry for entry in consumer_pf if _lookup_path(entry) not in paths_to_strip)
        # ``prefetch_related(None)`` clears the prefetch list on the
        # queryset; subsequent ``prefetch_related(*keep)`` rebuilds it
        # from the surviving consumer entries.  This is the documented
        # Django reset idiom for prefetch lookups.
        new_queryset = queryset.prefetch_related(None)
        if keep:
            new_queryset = new_queryset.prefetch_related(*keep)

    return new_prefetch, new_queryset


def lookup_paths(plan: OptimizationPlan) -> set[str]:
    """Return Django relation lookup paths covered by ``plan`` for B8/debugging."""
    if plan.finalized_lookup_paths is not None:
        return set(plan.finalized_lookup_paths)
    return _lookup_paths_from_parts(plan.select_related, plan.prefetch_related)


def _lookup_paths_from_parts(
    select_related: Iterable[str],
    prefetch_related: Iterable[Any],
) -> set[str]:
    """Return relation lookup paths from finalized or construction-time fields."""
    paths = set(select_related)
    paths.update(_prefetch_lookup_paths(prefetch_related))
    return paths


def _prefetch_lookup_paths(entries: Iterable[Any], prefix: str = "") -> set[str]:
    """Recursively flatten prefetch strings and nested ``Prefetch`` objects."""
    paths: set[str] = set()
    for entry in entries:
        if isinstance(entry, str):
            path = f"{prefix}__{entry}" if prefix else entry
            paths.add(path)
            continue
        prefetch_to = getattr(entry, "prefetch_to", None)
        if prefetch_to is None:
            continue
        path = f"{prefix}__{prefetch_to}" if prefix else prefetch_to
        paths.add(path)
        inner = getattr(entry, "queryset", None)
        inner_lookups = _consumer_prefetch_lookups(inner) if inner is not None else []
        if inner_lookups:
            paths.update(_prefetch_lookup_paths(inner_lookups, path))
    return paths
