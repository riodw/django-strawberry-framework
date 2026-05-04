"""``OptimizationPlan`` — the shape the walker emits and the extension consumes.

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
- ``cacheable``: whether this plan can be reused from the extension's plan
  cache.

The plan starts empty and accumulates entries as the walker descends the
selection tree. The extension applies it to the root queryset in a single
pass once the walk completes.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from typing import Any


@dataclass
class OptimizationPlan:
    """Immutable-ish bag of optimizer directives for one root queryset.

    Constructed by ``plan_optimizations`` in ``optimizer/walker.py`` and
    consumed by ``DjangoOptimizerExtension`` in ``optimizer/extension.py``.
    """

    select_related: list[str] = field(default_factory=list)
    """Forward FK / OneToOne field names for ``QuerySet.select_related``."""

    prefetch_related: list[Any] = field(default_factory=list)
    """Strings or ``Prefetch`` objects for ``QuerySet.prefetch_related``.

    Generated relation plans use ``Prefetch`` objects so child querysets can
    consistently carry projection and nested lookup state. Plain strings are
    still accepted for compatibility with manual plans or defensive fallback
    branches.
    """

    only_fields: list[str] = field(default_factory=list)
    """Scalar column names for ``QuerySet.only``."""
    fk_id_elisions: list[str] = field(default_factory=list)
    """Resolver keys elided because the source row already carries the target id."""
    planned_resolver_keys: list[str] = field(default_factory=list)
    """Resolver keys for relations covered by this plan, used by B3 strictness."""
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
        """Return ``True`` when no optimization directives were collected."""
        return (
            not self.select_related
            and not self.prefetch_related
            and not self.only_fields
            and not self.fk_id_elisions
            and not self.planned_resolver_keys
        )

    def apply(self, queryset: Any) -> Any:
        """Apply the plan to a ``QuerySet`` and return the optimized copy.

        Applies in order: ``only()`` → ``select_related()`` →
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


def resolver_key(
    parent_type: type | None,
    field_name: str,
    runtime_path: tuple[str, ...],
) -> str:
    """Return the branch-sensitive resolver key shared by walker and resolvers."""
    path = ".".join(runtime_path)
    if parent_type is None:
        return f"{field_name}@{path}"
    return f"{parent_type.__name__}.{field_name}@{path}"


def runtime_path_from_info(info: Any | None) -> tuple[str, ...]:
    """Return a GraphQL response path tuple with list indexes stripped."""
    if info is None:
        return ()
    return runtime_path_from_path(getattr(info, "path", None))


def runtime_path_from_path(path: Any) -> tuple[str, ...]:
    """Return a GraphQL response path tuple with list indexes stripped."""
    keys: list[str] = []
    while path is not None:
        key = getattr(path, "key", None)
        if not isinstance(key, int) and key is not None:
            keys.append(str(key))
        path = getattr(path, "prev", None)
    return tuple(reversed(keys))


def _flatten_select_related(sr: Any) -> set[str]:
    """Flatten Django's ``query.select_related`` into a set of dotted paths.

    Django stores ``select_related`` in three shapes:

    - ``False`` (the default — nothing has been selected): empty set.
    - ``True`` (the wildcard ``select_related()`` form): empty set as
      well. Django's wildcard only follows non-null FKs, so we cannot
      treat it as covering every optimizer entry — nullable FKs in the
      plan still need to be applied. Treating ``True`` as no overlap
      keeps optimizer entries; the consumer's wildcard will be narrowed
      by Django's subsequent ``select_related(*names)`` call, a known
      interaction that consumers combining wildcard ``select_related()``
      with this optimizer should be aware of.
    - ``dict`` (a nested mapping of selected field names): flattens to
      dotted lookup paths via recursive walk, e.g.
      ``{"category": {"parent": {}}}`` → ``{"category", "category__parent"}``.
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


def diff_plan_for_queryset(
    plan: OptimizationPlan,
    queryset: Any,
) -> tuple[OptimizationPlan, Any]:
    """Reconcile ``plan`` against optimizations already on ``queryset``.

    Returns ``(delta_plan, queryset_to_apply_against)``. The plan is
    only ever copied (never mutated) so B1's cache stays intact. The
    queryset is rewritten only when the consumer applied a plain
    ``prefetch_related("path")`` string that the optimizer can replace
    with a more specific ``Prefetch(path, queryset=...)`` carrying
    nested chains or projection.

    Reconciliation rules:

    ``select_related`` — compared as dotted lookup paths against the
    consumer's existing ``query.select_related`` dict. Exact matches
    are dropped from the plan; the wildcard form (``True``) is treated
    as no overlap so explicit nullable-FK entries still apply.

    ``prefetch_related`` — compared by ``prefetch_to`` with ancestry
    awareness. For each optimizer entry we gather the consumer entries
    on the same subtree (exact path or any descendant of it) and
    decide as a group:

    - **No consumer entries on the subtree** — the optimizer entry
      passes through unchanged.
    - **Optimizer can losslessly absorb the consumer subtree** — when
      the optimizer entry is a ``Prefetch`` carrying a queryset *and*
      every matching consumer entry is a bare string, the consumer
      strings (which carry no information of their own) are stripped
      from the queryset and the optimizer's nested ``Prefetch`` takes
      over. This is what makes
      ``prefetch_related("items", "items__entries")`` cooperate with
      ``Prefetch("items", queryset=...prefetch_related("entries"))``
      instead of raising ``ValueError: 'items' lookup was already seen
      with a different queryset``.
    - **Consumer wins** — for any other shape (consumer's own custom
      ``Prefetch`` somewhere on the subtree, or a plain-string-vs-
      plain-string match where the optimizer has no queryset to add),
      the optimizer entry is dropped to avoid the collision. The
      consumer's explicit subtree is preserved as-is.
    """
    already_select = _flatten_select_related(getattr(queryset.query, "select_related", False))
    new_select = [name for name in plan.select_related if name not in already_select]

    consumer_pf = list(getattr(queryset, "_prefetch_related_lookups", ()) or ())
    consumer_by_path: dict[str, Any] = {}
    for entry in consumer_pf:
        path = getattr(entry, "prefetch_to", entry)
        consumer_by_path[path] = entry

    new_prefetch: list[Any] = []
    paths_to_strip: set[str] = set()

    for opt_entry in plan.prefetch_related:
        opt_path = getattr(opt_entry, "prefetch_to", opt_entry)
        descendant_prefix = f"{opt_path}__"
        matching_paths = [
            path for path in consumer_by_path if path == opt_path or path.startswith(descendant_prefix)
        ]
        if not matching_paths:
            new_prefetch.append(opt_entry)
            continue
        opt_qs = getattr(opt_entry, "queryset", None)
        all_consumer_strings = all(isinstance(consumer_by_path[p], str) for p in matching_paths)
        if opt_qs is not None and all_consumer_strings:
            paths_to_strip.update(matching_paths)
            new_prefetch.append(opt_entry)
        # else: consumer wins on this subtree; optimizer dropped.

    new_queryset = queryset
    if paths_to_strip:
        keep = tuple(
            entry for entry in consumer_pf if getattr(entry, "prefetch_to", entry) not in paths_to_strip
        )
        new_queryset = queryset.prefetch_related(None)
        if keep:
            new_queryset = new_queryset.prefetch_related(*keep)

    if (
        len(new_select) == len(plan.select_related)
        and len(new_prefetch) == len(plan.prefetch_related)
        and new_queryset is queryset
    ):
        return plan, queryset
    return (
        replace(plan, select_related=new_select, prefetch_related=new_prefetch),
        new_queryset,
    )


def lookup_paths(plan: OptimizationPlan) -> set[str]:
    """Return Django relation lookup paths covered by ``plan`` for B8/debugging."""
    paths = set(plan.select_related)
    paths.update(_prefetch_lookup_paths(plan.prefetch_related))
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
        inner_lookups = getattr(inner, "_prefetch_related_lookups", None)
        if inner_lookups:
            paths.update(_prefetch_lookup_paths(inner_lookups, path))
    return paths
