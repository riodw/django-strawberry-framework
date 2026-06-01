"""Planned tests for ``django_strawberry_framework.orders.base``."""

# TODO(spec-028-orders-0_0_8 Slice 1): Cover ``RelatedOrder`` and shared lazy
# resolution behavior.
# Pseudocode:
#   - assert class targets, absolute import strings, and unqualified same-module
#     strings resolve to the same target orderset.
#   - assert unresolved targets raise ``ConfigurationError`` through finalizer
#     wrapping, preserving the original ``ImportError`` as ``__cause__``.
#   - assert ``bind_orderset`` stores the declaring orderset.
#   - assert order-side lazy resolution uses the shared ``sets_mixins`` mixin, not
#     a duplicated implementation.
