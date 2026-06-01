"""Planned ordering subsystem entry point.

The full implementation is tracked by ``docs/spec-028-orders-0_0_8.md``.
This placeholder keeps the planned package path visible without exporting
half-built public API.
"""

# TODO(spec-028-orders-0_0_8 Slice 1): Re-export the ordering primitives once
# ``base.py``, ``sets.py``, ``factories.py``, and ``inputs.py`` ship.
# Pseudocode:
#   - import ``RelatedOrder`` from ``orders.base``.
#   - import ``OrderSet`` / ``OrderSetMetaclass`` from ``orders.sets``.
#   - import ``OrderArgumentsFactory`` from ``orders.factories``.
#   - import ``Ordering``, ``INPUTS_MODULE_PATH``, and ``_input_type_name_for`` from
#     ``orders.inputs``.
#   - expose only the subpackage API; do not widen top-level
#     ``django_strawberry_framework.__all__``.
#
# TODO(spec-028-orders-0_0_8 Slice 3): Add the ``order_input_type`` helper and
# orphan-tracking ledger after ``OrderSet`` exists.
# Pseudocode:
#   - maintain ``_helper_referenced_ordersets: set[type[OrderSet]]`` next to the
#     helper.
#   - validate that the argument is an ``OrderSet`` subclass and raise
#     ``TypeError`` at resolver-declaration time for anything else.
#   - record the class in the helper ledger for finalizer orphan validation.
#   - return the element annotation
#     ``Annotated[name, strawberry.lazy(INPUTS_MODULE_PATH)]``; resolver code wraps
#     it as ``list[order_input_type(MyOrder)] | None``.

__all__: tuple[str, ...] = ()
