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

from django.db.models import Prefetch

from ..exceptions import ConfigurationError

# ``Prefetch`` is imported at runtime (not under ``TYPE_CHECKING``) because
# ``__post_init__`` performs an ``isinstance(..., Prefetch)`` validation;
# the field annotation ``Prefetch | None`` is also string-deferred by
# ``from __future__ import annotations``, but the runtime check is the
# load-bearing surface here.


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
    prefetch_obj: Prefetch | None = field(default=None, repr=False)
    skip: bool = False

    # ------------------------------------------------------------------
    # Class-level sentinel
    # ------------------------------------------------------------------

    # Populated after the class body via ``OptimizerHint(skip=True)``.
    # Declared here as a ClassVar so the dataclass decorator ignores it.
    SKIP: ClassVar[OptimizerHint]  # noqa: N815

    def __post_init__(self) -> None:
        """Reject conflicting flag combinations at construction time.

        The walker consumes flags in a strict priority order
        (``skip`` → ``prefetch_obj`` → ``force_select`` → ``force_prefetch``),
        so any combination beyond the four documented shapes silently
        loses the lower-priority directive.  Raising here surfaces the
        mistake at ``Meta.optimizer_hints`` build time instead of at
        query time.
        """
        if self.skip and (self.force_select or self.force_prefetch or self.prefetch_obj is not None):
            raise ConfigurationError(
                "OptimizerHint.SKIP (skip=True) cannot be combined with "
                "select_related(), prefetch_related(), or prefetch(obj).",
            )
        if self.force_select and self.force_prefetch:
            raise ConfigurationError(
                "OptimizerHint cannot set both force_select and force_prefetch "
                "(use either select_related() or prefetch_related(), not both).",
            )
        if self.prefetch_obj is not None and not isinstance(self.prefetch_obj, Prefetch):
            raise ConfigurationError(
                "OptimizerHint.prefetch(obj) requires a django.db.models.Prefetch "
                f"instance; got {type(self.prefetch_obj).__name__}.",
            )
        if self.prefetch_obj is not None and (self.force_select or self.force_prefetch):
            raise ConfigurationError(
                "OptimizerHint.prefetch(obj) (prefetch_obj=...) cannot be combined "
                "with select_related() or prefetch_related().",
            )

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
    def prefetch(cls, obj: Prefetch) -> OptimizerHint:
        """Use a specific ``Prefetch`` object for this field.

        This is a leaf operation. The consumer-provided queryset is the
        source of truth, and nested selections under this field are not
        walked by the optimizer.
        """
        return cls(prefetch_obj=obj)


def hint_is_skip(hint: Any) -> bool:
    """Return ``True`` if ``hint`` represents a "skip this relation" directive.

    Centralises the hint-shape contract so callers (the walker, the
    schema audit) never duplicate the ``hint is OptimizerHint.SKIP or
    hint.skip`` dispatch.  Defensively handles unexpected hint shapes by
    returning ``False`` rather than raising ``AttributeError``, so the
    schema audit can keep its "never raises" contract even if a future
    hint surface lands that does not expose a ``.skip`` attribute.
    """
    # ``None`` is unreachable through the documented call sites (the
    # walker iterates ``hints.items()`` and the extension audit calls
    # this only after a non-``None`` lookup), but kept as a defensive
    # short-circuit so the helper has the same shape consumers expect
    # from ``getattr``-style probes.
    if hint is None:
        return False
    if hint is OptimizerHint.SKIP:
        return True
    return bool(getattr(hint, "skip", False))


# Sentinel instance — must be created after the class body so the
# dataclass decorator has finished installing ``__init__`` and
# ``__setattr__``.  The ``# type: ignore[misc]`` silences mypy's
# "cannot assign to a ClassVar" warning: the ClassVar declaration is
# the only way to keep the dataclass decorator from treating ``SKIP``
# as a regular default-typed field, but mypy still flags the rebind.
OptimizerHint.SKIP = OptimizerHint(skip=True)  # type: ignore[misc]
