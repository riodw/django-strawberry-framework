"""``OptimizationPlan`` — the shape the walker emits and the extension consumes.

The plan is a simple data class carrying three bags:

- ``select_related``: forward FK / OneToOne joins that collapse into the
  parent query via ``QuerySet.select_related(*names)``.
- ``prefetch_related``: many-side relations (reverse FK, M2M) and
  visibility-downgraded forward rels, expressed as strings or
  ``django.db.models.Prefetch`` objects. Consumed by
  ``QuerySet.prefetch_related(*lookups)``.
- ``only_fields``: scalar column names for ``QuerySet.only(*names)``,
  including the FK columns required to materialize ``select_related``
  joins so Django doesn't mark them as deferred and re-query.

The plan starts empty and accumulates entries as the walker descends the
selection tree. The extension applies it to the root queryset in a single
pass once the walk completes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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

    Plain strings for simple reverse-FK / M2M lookups; ``Prefetch``
    objects when the target type has a custom ``get_queryset`` (the
    visibility-aware downgrade from spec-optimizer.md O6) or when the
    lookup is a nested chain (O4).
    """
    # TODO(spec-optimizer.md O4): nested prefetch chains land as
    # ``Prefetch("items", queryset=Item.objects.prefetch_related(
    #     Prefetch("entries", queryset=...)))`` rather than the flat
    # ``"items"`` strings the current O2 walker emits. The list type
    # already accepts ``Prefetch`` objects, so no signature change is
    # needed — the walker just builds nested ``Prefetch`` instances.

    only_fields: list[str] = field(default_factory=list)
    """Scalar column names for ``QuerySet.only``."""
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
        return not self.select_related and not self.prefetch_related and not self.only_fields

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
