"""``OptimizerHint`` — typed wrapper for ``Meta.optimizer_hints`` values.

Provides a uniform API for declaring per-field optimization overrides
in ``DjangoType.Meta.optimizer_hints``. Replaces the earlier exploratory
design that mixed raw strings (``"skip"``), ``Prefetch`` objects, and
dicts (``{"select_related": True}``) in the same field-value position.

Consumer surface::

    from django_strawberry_framework import OptimizerHint

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = "__all__"
            optimizer_hints = {
                "category": OptimizerHint.SKIP,
                "entries": OptimizerHint.prefetch_related(),
            }

The class lives in the optimizer subpackage because its primary consumer
is the walker (``optimizer/walker.py``), and it is re-exported from the
top-level ``__init__.py`` so the import path stays short.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar


@dataclass(frozen=True)
class OptimizerHint:
    """Typed optimization directive for a single relation field.

    Instances are created via the class-level sentinel ``SKIP`` or the
    factory classmethods ``select_related()``, ``prefetch_related()``,
    and ``prefetch(obj)``. Direct construction is intentionally possible
    (the dataclass is not hidden) but the factories are the documented
    consumer API.

    Attributes:
        force_select: Force ``select_related`` regardless of cardinality.
        force_prefetch: Force ``prefetch_related`` regardless of cardinality.
        prefetch_obj: A specific ``django.db.models.Prefetch`` instance
            to use instead of the auto-generated lookup string.
        skip: Exclude this relation from the optimization plan entirely.
    """

    force_select: bool = False
    force_prefetch: bool = False
    prefetch_obj: Any = field(default=None, repr=False)
    skip: bool = False

    # ------------------------------------------------------------------
    # Class-level sentinel
    # ------------------------------------------------------------------

    # Populated after the class body via ``OptimizerHint(skip=True)``.
    # Declared here as a ClassVar so the dataclass decorator ignores it.
    SKIP: ClassVar[OptimizerHint]  # noqa: N815

    # ------------------------------------------------------------------
    # Factory classmethods
    # ------------------------------------------------------------------

    @classmethod
    def select_related(cls) -> OptimizerHint:
        """Force ``select_related`` for this field."""
        return cls(force_select=True)

    @classmethod
    def prefetch_related(cls) -> OptimizerHint:
        """Force ``prefetch_related`` for this field."""
        return cls(force_prefetch=True)

    @classmethod
    def prefetch(cls, obj: Any) -> OptimizerHint:
        """Use a specific ``Prefetch`` object for this field.

        This is a leaf operation. The consumer-provided queryset is the
        source of truth, and nested selections under this field are not
        walked by the optimizer.
        """
        return cls(prefetch_obj=obj)


# Sentinel instance — must be created after the class body.
OptimizerHint.SKIP = OptimizerHint(skip=True)  # type: ignore[misc]
