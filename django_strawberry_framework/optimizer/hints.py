"""``OptimizerHint`` - typed wrapper for ``Meta.optimizer_hints`` values.

Provides a uniform API for declaring per-field optimization overrides
in ``DjangoType.Meta.optimizer_hints``.

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

from dataclasses import dataclass
from typing import ClassVar

from django.db.models import Prefetch

from ..exceptions import ConfigurationError, _safe_type_name

# The shared public strategy-selection type (and the validator it feeds) are
# owned by ``nested_fetch`` beside ``NestedConnectionStrategy``. They are
# imported at RUNTIME, not under ``TYPE_CHECKING``: ``StrategySelection``
# annotates the public ``nested_strategy`` field / ``strategy()`` factory, and a
# runtime consumer calling ``typing.get_type_hints(OptimizerHint)`` (a docs
# generator, a runtime-validation library, an IDE bridge) must be able to
# resolve that name from this module's globals - a ``TYPE_CHECKING``-only import
# leaves the postponed annotation unresolvable and raises ``NameError``. There
# is NO import cycle to guard against: ``nested_fetch`` and its transitive
# imports (``plans`` / ``join_taxonomy`` / ``utils.connections`` /
# ``exceptions``) never import this module, so a plain runtime import is the
# smallest correct fix.
from .nested_fetch import StrategySelection, resolve_strategy

# ``Prefetch`` is imported at runtime (not under ``TYPE_CHECKING``) because
# ``_require_prefetch`` performs an ``isinstance(..., Prefetch)`` validation;
# the field annotation ``Prefetch | None`` is also string-deferred by
# ``from __future__ import annotations``, but the runtime check is the
# load-bearing surface here.


def _require_prefetch(obj: object) -> Prefetch:
    """Return ``obj`` when it is a ``Prefetch``; else raise ``ConfigurationError``.

    Single owner for the Prefetch-type invariant shared by
    ``OptimizerHint.prefetch`` (factory argument) and ``__post_init__``
    (direct ``prefetch_obj=`` construction). The factory must call this
    before ``cls(prefetch_obj=...)`` because ``None`` is the dataclass's
    legitimate "no prefetch object" default - without a factory-side
    check, ``prefetch(None)`` would become a silent no-op.
    """
    if not isinstance(obj, Prefetch):
        raise ConfigurationError(
            "OptimizerHint.prefetch(obj) requires a django.db.models.Prefetch "
            f"instance; got {_safe_type_name(obj)}.",
        )
    return obj


def _require_strategy(name: object) -> StrategySelection:
    """Return ``name`` when it is a valid strategy selection; else raise ``ConfigurationError``.

    Single owner for the strategy-selection invariant shared by
    ``OptimizerHint.strategy`` (factory argument) and ``__post_init__``
    (direct ``nested_strategy=`` construction). The factory must call this
    before ``cls(nested_strategy=...)`` because ``None`` is the dataclass's
    legitimate "no strategy override" default - without a factory-side
    check, ``strategy(None)`` would become a silent no-op.

    The typed rejection is unconditional and owned by
    ``nested_fetch.resolve_strategy`` itself: every dunder its dispatch reads
    (``__eq__`` through the base ``str`` slot, ``__hash__`` in the registry
    lookup, ``__repr__`` in the message, the ``plan`` attribute read) is
    guarded there, so a hostile selection value degrades to the typed
    ``ConfigurationError`` and no raw exception can reach this boundary to
    be contained. This factory check keeps only its own contract: an
    explicit ``None`` must reject here rather than resolve the
    ``NESTED_CONNECTION_STRATEGY`` setting the way ``resolve_strategy(None)``
    legitimately does.
    """
    if name is None:
        raise ConfigurationError(
            "OptimizerHint.strategy(name) requires a strategy name ('windowed' | 'lateral' | 'auto') "
            f"or a NestedConnectionStrategy instance; got {_safe_type_name(name)}.",
        )
    resolve_strategy(name)
    return name  # type: ignore[return-value]


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
        nested_strategy: Override the nested-connection fetch strategy for a
            Relay connection field (a registered strategy name such as
            ``"windowed"`` / ``"lateral"``, ``"auto"``, or a
            ``NestedConnectionStrategy`` instance). Validated at construction
            time through ``optimizer/nested_fetch.py::resolve_strategy``, so a
            typo raises ``ConfigurationError`` at ``Meta.optimizer_hints`` build
            time. The knob is schema-static and needs NO plan-cache-key change:
            the plan cache is instance-bound (``optimizer/extension.py``
            Decision 11), so strategy selection never depends on request-varying
            data. Strategy selection MUST never depend on request-varying data
            outside the cache key.
    """

    force_select: bool = False
    force_prefetch: bool = False
    prefetch_obj: Prefetch | None = None
    skip: bool = False
    nested_strategy: StrategySelection | None = None

    # ------------------------------------------------------------------
    # Class-level sentinel
    # ------------------------------------------------------------------

    # Populated after the class body via ``OptimizerHint(skip=True)``.
    # Declared here as a ClassVar so the dataclass decorator ignores it.
    SKIP: ClassVar[OptimizerHint]

    def __post_init__(self) -> None:
        """Reject invalid flag types and conflicting directives.

        Construction-time rejection is the load-bearing contract: any
        shape beyond the four directives and the empty no-op form raises
        ``ConfigurationError`` at ``OptimizerHint(...)`` time. This surfaces
        mistakes at ``Meta.optimizer_hints`` build time instead of query time.
        The walker's own priority order
        (``skip`` -> ``prefetch_obj`` -> ``force_select`` -> ``force_prefetch``
        in ``optimizer/walker.py::_apply_hint``) is therefore documentation
        of the dispatch sequence, not collision arbitration - every
        conflict the priority order would have arbitrated has already
        been rejected here.
        """
        flag_names = ("force_select", "force_prefetch", "skip")
        invalid_flags = [name for name in flag_names if type(getattr(self, name)) is not bool]
        if invalid_flags:
            raise ConfigurationError(
                "OptimizerHint force_select, force_prefetch, and skip flags must be bool values; "
                f"got non-bool values for: {invalid_flags}.",
            )
        if self.skip and (
            self.force_select or self.force_prefetch or self.prefetch_obj is not None
        ):
            raise ConfigurationError(
                "OptimizerHint.SKIP (skip=True) cannot be combined with "
                "select_related(), prefetch_related(), or prefetch(obj).",
            )
        if self.force_select and self.force_prefetch:
            raise ConfigurationError(
                "OptimizerHint cannot set both force_select and force_prefetch "
                "(use either select_related() or prefetch_related(), not both).",
            )
        if self.prefetch_obj is not None:
            _require_prefetch(self.prefetch_obj)
            if self.force_select or self.force_prefetch:
                raise ConfigurationError(
                    "OptimizerHint.prefetch(obj) (prefetch_obj=...) cannot be combined "
                    "with select_related() or prefetch_related().",
                )
        if self.nested_strategy is not None:
            # A connection is always a prefetch, so ``skip``/``prefetch(obj)``/
            # ``select_related()`` are incoherent with a strategy override;
            # ``force_prefetch`` is redundant-but-harmless and stays allowed.
            if self.skip or self.prefetch_obj is not None or self.force_select:
                raise ConfigurationError(
                    "OptimizerHint.strategy(name) (nested_strategy=...) cannot be combined "
                    "with SKIP (skip=True), prefetch(obj), or select_related(); force_prefetch "
                    "is redundant but allowed.",
                )
            # Route the name through ``_require_strategy`` for typo-loud
            # ConfigurationError parity (module-level import above; no cycle).
            _require_strategy(self.nested_strategy)

    # ------------------------------------------------------------------
    # Factory classmethods
    # ------------------------------------------------------------------

    @classmethod
    def strategy(cls, name: StrategySelection) -> OptimizerHint:
        """Override the nested-connection fetch strategy for this field.

        ``name`` is a registered strategy name (``"windowed"`` / ``"lateral"``),
        ``"auto"``, or a ``NestedConnectionStrategy`` instance. It is validated
        at construction time through ``_require_strategy`` (and
        ``optimizer/nested_fetch.py::resolve_strategy``), so a typo or ``None``
        raises ``ConfigurationError`` at ``Meta.optimizer_hints`` build time
        rather than at query time. Applies only to Relay connection fields; a
        non-connection field silently ignores the override.
        """
        return cls(nested_strategy=_require_strategy(name))

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

        Type-and-message ownership lives in ``_require_prefetch``; the
        factory must invoke it before construction so ``None`` cannot
        collapse into the empty no-op hint (see that helper's docstring).
        """
        return cls(prefetch_obj=_require_prefetch(obj))


def hint_is_skip(hint: OptimizerHint | None) -> bool:
    """Return ``True`` if ``hint`` represents a "skip this relation" directive.

    Centralises the hint-shape contract so callers (the walker, the
    schema audit) never duplicate the ``hint is OptimizerHint.SKIP or
    hint.skip`` dispatch.  Defensively handles unexpected hint shapes by
    returning ``False`` rather than raising ``AttributeError``, so the
    schema audit can keep its "never raises" contract even if a future
    hint surface lands that does not expose a ``.skip`` attribute.
    """
    # The walker usually receives concrete hint values from ``hints.items()``;
    # the schema audit probes ``hints.get(field_name)`` for every exposed
    # relation, so ``None`` is a normal "no hint configured" path there.
    if hint is None:
        return False
    if hint is OptimizerHint.SKIP:
        return True
    try:
        return bool(getattr(hint, "skip", False))
    except BaseException:
        return False


# Sentinel instance - must be created after the class body so the
# dataclass decorator has finished installing ``__init__`` and
# ``__setattr__``.  The ``# type: ignore[misc]`` silences mypy's
# "cannot assign to a ClassVar" warning: the ClassVar declaration is
# the only way to keep the dataclass decorator from treating ``SKIP``
# as a regular default-typed field, but mypy still flags the rebind.
OptimizerHint.SKIP = OptimizerHint(skip=True)  # type: ignore[misc]
