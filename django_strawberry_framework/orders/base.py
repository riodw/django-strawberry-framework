"""``RelatedOrder`` - the nested-path ordering primitive.

Layer 1 of the spec-028 six-layer plan. ``RelatedOrder`` is the collapsed
port of the cookbook's ``django_graphene_filters/orders.py::BaseRelatedOrder``
+ ``::RelatedOrder`` pair (per spec-028 Decision 2 - single-symbol public
surface). ``LazyRelatedClassMixin`` is reused from the neutral
``django_strawberry_framework.sets_mixins`` module via sibling import per
spec-028 (importing through ``filters.base`` would load the
entire filter subsystem just to build orders, and would re-couple sibling
Layer-3 packages after the neutral module was extracted).

The cookbook signature makes ``field_name`` required positional on the
``RelatedOrder`` subclass; this port makes it optional so the metaclass's
collection step can mutate it later if needed. The consumer-facing
``OrderSet.Meta.fields`` surface always supplies one explicitly, so the
relaxation is purely ergonomic.

No operator-bag / form-cleaning machinery - the order side has no
operator-bag (no ``and_`` / ``or_`` / ``not_``) and no form validation per
spec-028 Decision 8.
"""

from __future__ import annotations

from typing import Any

from ..exceptions import (
    ConfigurationError,
    _safe_arg_repr,
    _safe_class_name,
    _safe_type_name,
)
from ..sets_mixins import RelatedSetTargetMixin


def _order_set_class() -> type:
    """Return the ``OrderSet`` family base for the target-type gate.

    Deferred so the ``orders.sets -> orders.base`` module-load edge stays
    one-directional: ``orders.sets`` imports this module at module scope
    (the metaclass needs ``RelatedOrder``), so a module-level import back
    would re-enter a partially-initialized ``orders.sets`` at import time
    -- the same cycle-keeping contract as
    ``types/base.py::_validate_orderset_class``'s local import.
    """
    from .sets import OrderSet

    return OrderSet


class RelatedOrder(RelatedSetTargetMixin):
    """Target another ``OrderSet`` to enable nested-relation ordering.

    Collapsed port of ``django_graphene_filters/orders.py::BaseRelatedOrder``
    + ``::RelatedOrder`` into a single consumer-facing class
    per spec-028 Decision 2. The lazy-resolution logic (``bind_orderset``,
    ``.orderset`` property, string-resolution through the shared mixin)
    carries over from the cookbook unchanged.

    Target acceptance shapes:

    - An ``OrderSet`` class.
    - An absolute import path (e.g. ``"apps.library.orders.ShelfOrder"``).
    - An unqualified class name resolved against the owning orderset's
      module (e.g. ``"ShelfOrder"`` when both ordersets live in the same
      file).
    - ``None`` -- the placeholder form (the branch is skipped at input
      emission and BFS enqueue).

    A target that RESOLVES to anything else -- a ``FilterSet`` (the
    cross-family twin), a plain class, or a factory returning a non-class
    -- raises ``ConfigurationError`` at the ``.orderset`` read. Without the
    gate the mis-wiring survives declaration, binding, and expansion and
    first detonates inside the BFS input builder (``set_input_type_name``
    calling ``target.type_name_for()``) -- at finalize subpass 4, OUTSIDE
    the uniform subpass-2 rewrap, leaking a raw ``AttributeError`` (or,
    for a structurally FilterSet-shaped target, silently walking the
    filter family's fields through the order input builder).
    """

    # ``RelatedSetTargetMixin`` parameterization: the slots the shared
    # owner-bind / lazy-target machinery reads. The filter
    # twin uses ``("_filterset", "bound_filterset")``.
    _target_attr = "_orderset"
    _owner_attr = "bound_orderset"

    def __init__(self, orderset: str | type, field_name: str | None = None) -> None:
        """Store the (possibly-lazy) target orderset and the ORM field name."""
        super().__init__()
        self._orderset = orderset
        self.field_name = field_name

    def bind_orderset(self, orderset: type) -> None:
        """Bind the owning ``OrderSet`` once; subsequent calls are no-ops.

        Idempotent so ``OrderSetMetaclass.__new__`` can rebind every
        related order on subclass creation without clobbering a deliberate
        override. Mirrors the filter side's
        ``RelatedFilter.bind_filterset`` idempotency contract. Thin wrapper
        over the shared ``RelatedSetTargetMixin._bind_owner``.
        """
        self._bind_owner(orderset)

    def _validate_target(self, resolved: Any) -> None:
        """The ``RelatedSetTargetMixin`` family gate: target must be an ``OrderSet``.

        Fired by ``sets_mixins.py::RelatedSetTargetMixin._resolved_target`` on
        every non-``None`` resolved read -- the one seam every consumer routes
        through (Layer-5 BFS enqueue, input-triple emission, runtime
        ``normalize_input_value`` recursion, permission-branch recursion).
        Without the gate the mis-wiring survives declaration, binding, and
        expansion and first detonates inside the BFS input builder
        (``set_input_type_name`` calling ``target.type_name_for()``) -- at
        finalize subpass 4, OUTSIDE the uniform subpass-2 rewrap, leaking a raw
        ``AttributeError`` (or, for a structurally FilterSet-shaped target,
        silently walking the filter family's fields through the order input
        builder). Mirrors the filter twin's
        ``filters/base.py::RelatedFilter._validate_target``.
        """
        if not (isinstance(resolved, type) and issubclass(resolved, _order_set_class())):
            owner = getattr(self, self._owner_attr, None)
            owner_label = (
                _safe_class_name(owner, qualified=True) if isinstance(owner, type) else "<unbound>"
            )
            raise ConfigurationError(
                f"{owner_label} declares RelatedOrder {_safe_arg_repr(self.field_name)} targeting "
                f"{_safe_type_name(resolved)}, which is not an OrderSet subclass. "
                "RelatedOrder targets must resolve to an OrderSet subclass (a class, "
                "an import-path string, or a zero-arg factory returning one); "
                "a FilterSet or unrelated class cannot order a relation branch. "
                "Declare the branch with an OrderSet or remove it.",
            )

    @property
    def orderset(self) -> type | None:
        """Resolve ``self._orderset`` lazily on first access.

        Re-stores the resolved class so the next access is a plain
        attribute read; setter remains usable when a caller wants to
        substitute the target. String / callable resolution is delegated
        to ``LazyRelatedClassMixin.resolve_lazy_class`` via the shared
        ``RelatedSetTargetMixin._resolved_target``, which also fires the
        family's target-TYPE gate (``_validate_target``): a resolved value
        must be ``None`` (the skip-silently placeholder) or an ``OrderSet``
        subclass.
        """
        return self._resolved_target()

    @orderset.setter
    def orderset(self, value: Any) -> None:
        self._set_target(value)
