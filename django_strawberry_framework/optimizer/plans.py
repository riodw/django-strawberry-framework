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
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    from django.db.models import Prefetch


@dataclass
class OptimizationPlan:
    """Immutable-ish bag of optimizer directives for one root queryset.

    Constructed by ``plan_optimizations`` in ``optimizer/walker.py`` and
    consumed by ``DjangoOptimizerExtension`` in ``optimizer/extension.py``.

    Cache invariant: once a plan has been handed off (returned from the
    walker, stashed on ``info.context``, or stored in the extension's
    plan cache), it must not be mutated in place.  Use
    ``dataclasses.replace`` to derive a modified plan.  The class is
    intentionally not ``frozen=True`` so the walker can accumulate
    entries during construction; every other caller treats the plan as
    immutable.
    """

    select_related: list[str] = field(default_factory=list)
    """Forward FK / OneToOne field names for ``QuerySet.select_related``."""

    prefetch_related: list[str | Prefetch] = field(default_factory=list)
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
    """Return the runtime path tuple from a GraphQL ``info`` (or ``()`` when absent).

    Thin wrapper that pulls ``info.path`` and delegates to
    ``runtime_path_from_path``; ``info=None`` short-circuits to the
    empty tuple so resolver-key construction stays branch-free at the
    call site.
    """
    if info is None:
        return ()
    return runtime_path_from_path(getattr(info, "path", None))


def runtime_path_from_path(path: Any) -> tuple[str, ...]:
    """Walk a GraphQL ``path`` linked-list and return its keys, list indexes stripped.

    Iterates ``path.prev`` from the deepest selection back to the root,
    skipping integer keys (graphql-core's list-index entries) so the
    resulting tuple is a stable structural identity for cache-key and
    resolver-key purposes.
    """
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


def _lookup_path(entry: Any) -> str:
    """Return the prefetch lookup path for an entry (string or ``Prefetch``).

    Centralizes the brittle Django-private contract for ``Prefetch.prefetch_to``
    so a future Django rename has one fix.  Plain-string entries are
    returned as-is (they double as their own path).
    """
    return getattr(entry, "prefetch_to", entry)


def _consumer_prefetch_lookups(queryset: Any) -> list[Any]:
    """Return the ``_prefetch_related_lookups`` already attached to a queryset.

    Centralizes the brittle Django-private contract for
    ``QuerySet._prefetch_related_lookups``.  Returns an empty list when
    the queryset has no prefetches (or the attribute is missing entirely
    on a non-QuerySet input).
    """
    return list(getattr(queryset, "_prefetch_related_lookups", ()) or ())


def _optimizer_can_absorb(
    opt_entry: Any,
    consumer_paths: list[str],
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
       drop data — for example, optimizer
       ``Prefetch("items", queryset=Item.objects.only("name"))``
       cannot absorb consumer ``"items__entries"``.
    """
    if getattr(opt_entry, "queryset", None) is None:
        return False
    if not all(isinstance(consumer_by_path[p], str) for p in consumer_paths):
        return False
    opt_covered = _prefetch_lookup_paths([opt_entry])
    return all(path in opt_covered for path in consumer_paths)


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
    - **Consumer wins** — for any other shape (consumer's own custom
      ``Prefetch`` somewhere on the subtree, plain-string-vs-
      plain-string match where the optimizer has no queryset, or a
      consumer descendant the optimizer's own subtree does not cover),
      the optimizer entry is dropped to avoid the collision and to
      avoid silently stripping consumer prefetches the optimizer would
      not replace.
    """
    new_select = _diff_select_related(plan.select_related, queryset)
    new_prefetch, new_queryset = _diff_prefetch_related(plan.prefetch_related, queryset)

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


def _diff_select_related(plan_select_related: list[str], queryset: Any) -> list[str]:
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
    plan_prefetch_related: list[Any],
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
            path for path in consumer_by_path if path == opt_path or path.startswith(descendant_prefix)
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
        inner_lookups = _consumer_prefetch_lookups(inner) if inner is not None else []
        if inner_lookups:
            paths.update(_prefetch_lookup_paths(inner_lookups, path))
    return paths
