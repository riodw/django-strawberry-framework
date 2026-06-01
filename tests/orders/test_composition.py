"""Planned cross-card composition tests for filters plus orders."""

# TODO(spec-028-orders-0_0_8 Slice 6): Cover a ``DjangoType`` that declares both
# ``Meta.filterset_class`` and ``Meta.orderset_class``.
# Pseudocode:
#   - build a schema whose resolver accepts both ``filter:`` and ``orderBy:``.
#   - assert SDL exposes both generated input types.
#   - apply a filter then an order and inspect the queryset for both ``WHERE`` and
#     ``ORDER BY`` clauses.
#   - assert the shared lazy resolver has no cross-subsystem state leak.
