"""Planned tests for ``OrderSetMetaclass`` and ``OrderSet``."""

# TODO(spec-028-orders-0_0_8 Slice 1): Cover field expansion, permission gates,
# and the sync/async apply pair.
# Pseudocode:
#   - assert the metaclass collects ``RelatedOrder`` declarations with override
#     semantics and calls ``bind_orderset``.
#   - assert ``Meta.fields`` rejects unknown names and ``"__all__"`` includes
#     only column-backed fields.
#   - assert ``get_fields`` resolves lazy targets with the recursion guard.
#   - assert ``check_permissions`` fires only for active input fields, including
#     parent relation gates and child orderset gates for active branches.
#   - assert duplicate list entries fire each permission method once.
#   - assert ``apply_sync`` and ``apply_async`` normalize input, extract request,
#     call permission checks, convert directions to ``OrderBy`` expressions, and
#     return an ordered queryset.
#   - assert empty list and ``None`` directions are no-ops.
