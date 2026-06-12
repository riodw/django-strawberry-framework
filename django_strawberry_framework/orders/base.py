"""``RelatedOrder`` - the nested-path ordering primitive.

Layer 2 of the spec-028 six-layer plan. ``RelatedOrder`` is the collapsed
port of the cookbook's ``django_graphene_filters/orders.py::BaseRelatedOrder``
+ ``::RelatedOrder`` pair (per spec-028 Decision 2 - single-symbol public
surface). ``LazyRelatedClassMixin`` is reused from the neutral
``django_strawberry_framework.sets_mixins`` module via sibling import per
spec-028 Revision 4 H1 (importing through ``filters.base`` would load the
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

from ..sets_mixins import LazyRelatedClassMixin


class RelatedOrder(LazyRelatedClassMixin):
    """Target another ``OrderSet`` to enable nested-relation ordering.

    Collapsed port of ``django_graphene_filters/orders.py::BaseRelatedOrder``
    + ``::RelatedOrder`` into a single consumer-facing class per spec-028
    Decision 2. The lazy-resolution logic (``bind_orderset``, ``.orderset``
    property, string-resolution through the shared mixin) carries over
    from the cookbook unchanged.

    Target acceptance shapes:

    - An ``OrderSet`` class.
    - An absolute import path (e.g. ``"apps.library.orders.ShelfOrder"``).
    - An unqualified class name resolved against the owning orderset's
      module (e.g. ``"ShelfOrder"`` when both ordersets live in the same
      file).
    """

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
        ``RelatedFilter.bind_filterset`` idempotency contract.
        """
        if not hasattr(self, "bound_orderset"):
            self.bound_orderset = orderset

    @property
    def orderset(self) -> type:
        """Resolve ``self._orderset`` lazily on first access.

        Re-stores the resolved class so the next access is a plain
        attribute read; setter remains usable when a caller wants to
        substitute the target. String / callable resolution is delegated
        to ``LazyRelatedClassMixin.resolve_lazy_class``.
        """
        self._orderset = self.resolve_lazy_class(
            self._orderset,
            getattr(self, "bound_orderset", None),
        )
        return self._orderset

    @orderset.setter
    def orderset(self, value: Any) -> None:
        self._orderset = value
