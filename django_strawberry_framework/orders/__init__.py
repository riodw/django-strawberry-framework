"""Ordering subsystem - declarative ``OrderSet`` classes that become GraphQL ``orderBy:`` arguments.

Re-exports the foundational primitives from ``base.py``, the
``OrderSet`` + ``OrderSetMetaclass`` pair from ``sets.py``, the
``Ordering`` enum from ``inputs.py``, and the Decision-11 consumer
helper ``order_input_type``. The finalizer's phase 2.5 wires
the orphan check that compares ``_helper_referenced_ordersets``
against the set of ``Meta.orderset_class``-wired ordersets.

``INPUTS_MODULE_PATH`` and ``_input_type_name_for`` are re-exported at
module scope for consumers but NOT listed in
``__all__`` -- the leading ``_`` flags them private to consumers.
Mirrors ``django_strawberry_framework/filters/__init__.py``'s
convention. ``OrderArgumentsFactory`` is **not** re-exported from this
entry point: advanced consumers import it from
``django_strawberry_framework.orders.factories`` directly, exactly as
the filter side keeps ``FilterArgumentsFactory`` out of
``filters/__init__.py`` (per spec-028 Decision 2). ``OrderSetMetaclass``
IS in ``__all__`` because the filter twin keeps ``FilterSetMetaclass``
in its ``__all__`` -- one-for-one parity with the shipped filter
surface.
"""

from __future__ import annotations

from ..registry import register_subsystem_clear
from ..utils.inputs import build_lazy_input_annotation
from .base import RelatedOrder
from .inputs import INPUTS_MODULE_PATH, Ordering, _input_type_name_for
from .sets import OrderSet, OrderSetMetaclass

# Ledger of ``OrderSet``s referenced through the Decision-11
# ``order_input_type(...)`` consumer helper. Cleared via the
# ``register_subsystem_clear`` row below (owner
# ``orders.helper_references``) so ``registry.clear()`` replays
# the callback -- not via a cycle-safe local import inside
# ``TypeRegistry.clear`` (that shape predates the registration
# seam). The finalizer's phase 2.5 orphan validation compares
# this set against the set of ``Meta.orderset_class``-wired
# ordersets and raises ``ConfigurationError`` for orphans.
_helper_referenced_ordersets: set[type[OrderSet]] = set()


def _clear_helper_referenced_ordersets() -> None:
    _helper_referenced_ordersets.clear()


register_subsystem_clear(_clear_helper_referenced_ordersets, owner="orders.helper_references")


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
    # Decision-11 consumer-helper body shared with ``filters/__init__.py::
    # filter_input_type`` via ``utils/inputs.py::build_lazy_input_annotation``
    # (the 0.0.9 DRY pass). The return is the **element type** (spec-028
    # Revision 4 B1) -- consumers wrap as ``list[order_input_type(MyOrder)] |
    # None``. The shared helper preserves the ForwardRef-wrapped
    # ``Annotated[<runtime str>, strawberry.lazy(...)]`` form
    # ``LazyType.resolve_type`` requires.
    return build_lazy_input_annotation(
        orderset_class,
        expected_base=OrderSet,
        family_name="order_input_type",
        expected_label="an OrderSet",
        ledger=_helper_referenced_ordersets,
        input_type_name_for=_input_type_name_for,
        module_path=INPUTS_MODULE_PATH,
    )


__all__: tuple[str, ...] = (
    "OrderSet",
    "OrderSetMetaclass",
    "Ordering",
    "RelatedOrder",
    "order_input_type",
)
