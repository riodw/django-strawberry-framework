"""Order subsystem entry point.

Re-exports the foundational primitives from ``base.py``, the
``OrderSet`` + ``OrderSetMetaclass`` pair from ``sets.py``, the
``Ordering`` enum from ``inputs.py``, and the Decision-11 consumer
helper ``order_input_type``. Slice 3 will wire ``registry.clear()`` to
clear the namespace via the local-import dance per spec-028 Decision 9
(two separate steps -- ``clear_order_input_namespace()`` AND
``_helper_referenced_ordersets.clear()``).

``INPUTS_MODULE_PATH`` and ``_input_type_name_for`` are re-exported at
module scope for Slice 2 / Slice 3 consumers but NOT listed in
``__all__`` -- the leading ``_`` flags them private to consumers.
Mirrors ``django_strawberry_framework/filters/__init__.py``'s
convention. ``OrderArgumentsFactory`` is module-importable for
advanced uses per Spec Decision 2 but not in ``__all__`` (matches the
filter side's ``FilterArgumentsFactory`` treatment).
"""

from __future__ import annotations

from typing import Annotated

import strawberry

from .base import RelatedOrder
from .factories import OrderArgumentsFactory
from .inputs import INPUTS_MODULE_PATH, Ordering, _input_type_name_for
from .sets import OrderSet, OrderSetMetaclass

# Ledger of ``OrderSet``s referenced through the Decision-11
# ``order_input_type(...)`` consumer helper. Per spec-028 Decision 2
# N-new-2 of rev2 the ledger lives in ``__init__.py`` co-located with
# its only writer (``order_input_type``). Slice 3's ``registry.clear()``
# clears this set via a cycle-safe local import per spec-028
# Decision 9 line 775 -- in a SEPARATE block from
# ``clear_order_input_namespace()`` so the two-block layout matches
# the filter side.
_helper_referenced_ordersets: set[type[OrderSet]] = set()


def order_input_type(orderset_class: type[OrderSet]) -> object:
    """Return the ``Annotated[...]`` forward-reference for an orderset's input class.

    The returned annotation is the canonical Strawberry forward-
    reference idiom for the **element type** of an order argument:
    ``Annotated["<Name>OrderInputType", strawberry.lazy("django_strawberry_framework.orders.inputs")]``.
    Per spec-028 Revision 4 B1, consumers wrap the helper's return as
    ``list[order_input_type(MyOrder)] | None`` at the resolver site so
    the GraphQL argument shape is ``orderBy: [MyOrderInputType!]``
    (list-of-non-null per Spec Decision 5).

    Strawberry collects the annotation at ``@strawberry.type``
    decoration time, defers resolution, and resolves it via
    ``LazyType.resolve_type`` at schema-build time -- by which point
    ``finalize_django_types()`` has materialized the input class as a
    module global of ``django_strawberry_framework.orders.inputs``.

    Args:
        orderset_class: An ``OrderSet`` subclass. Validated eagerly --
            the call raises ``TypeError`` for any non-``OrderSet``
            argument so consumers catch misuse at the resolver-
            declaration site instead of at schema-build time.

    Raises:
        TypeError: ``orderset_class`` is not an ``OrderSet`` subclass.
    """
    if not (isinstance(orderset_class, type) and issubclass(orderset_class, OrderSet)):
        raise TypeError(
            f"order_input_type() requires an OrderSet subclass; got {orderset_class!r}",
        )
    _helper_referenced_ordersets.add(orderset_class)
    name = _input_type_name_for(orderset_class)
    # ``Annotated[<str_variable>, ...]`` wraps the runtime-computed
    # string as a ``typing.ForwardRef`` in the first ``__args__``
    # position; Strawberry's ``LazyType.resolve_type`` requires the
    # ForwardRef-wrapped form to resolve via ``module.__dict__`` at
    # schema build. Per spec-028 Revision 4 B1, the return is the
    # **element type** -- consumers wrap as
    # ``list[order_input_type(MyOrder)] | None``.
    return Annotated[name, strawberry.lazy(INPUTS_MODULE_PATH)]


__all__: tuple[str, ...] = (
    "Ordering",
    "OrderSet",
    "OrderSetMetaclass",
    "RelatedOrder",
    "order_input_type",
)
