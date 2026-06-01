"""Planned ``OrderSet`` metaclass and runtime pipeline."""

# TODO(spec-028-orders-0_0_8 Slice 1): Add ``OrderSetMetaclass`` and ``OrderSet``
# without an ``apply(...)`` dispatcher.
# Pseudocode:
#   - collect declared ``RelatedOrder`` instances into ``related_orders`` with
#     MRO override semantics matching the cookbook.
#   - call ``related_order.bind_orderset(new_class)`` during class creation.
#   - validate ``Meta.model`` and ``Meta.fields``; reject unknown model fields as
#     ``ConfigurationError``.
#   - implement ``get_fields()`` with the ``_is_expanding_fields`` recursion
#     guard and cache only after no lazy targets remain.
#   - expand ``Meta.fields = "__all__"`` to every column-backed field, including
#     forward FK / OneToOne columns and excluding reverse relations / M2M managers.
#
# TODO(spec-028-orders-0_0_8 Slice 1): Add resolver-facing
# ``OrderSet.apply_sync`` and ``OrderSet.apply_async``.
# Pseudocode:
#   - normalize a list-shaped Strawberry input into ``(field_path, Ordering)``
#     pairs via ``get_flat_orders`` / ``orders.inputs.normalize_input_value``.
#   - extract the request from ``info.context.request`` with bare ``HttpRequest``
#     fallback.
#   - run active-input-only permission checks, including parent
#     ``check_<branch>_permission`` and child field gates for active
#     ``RelatedOrder`` branches.
#   - deduplicate permission hooks by ``(OrderSet class, method name)``.
#   - convert directions with ``Ordering.resolve(field_path)`` and return
#     ``queryset.order_by(*expressions)``; skip the call for empty inputs.
#   - keep ``apply_async`` pure in-memory; do not wrap consumer hooks in
#     ``sync_to_async``.
