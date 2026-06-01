"""Planned BFS factory for generated order input classes."""

# TODO(spec-028-orders-0_0_8 Slice 2): Implement ``OrderArgumentsFactory`` as the
# ordering-side Layer-5 BFS.
# Pseudocode:
#   - keep class-level ``input_object_types`` and ``_type_orderset_registry``
#     caches keyed by class-derived input type name.
#   - reject subclassing because those mutable caches are not subclass-isolated.
#   - start from the root ``OrderSet`` and breadth-first enqueue every reachable
#     ``RelatedOrder`` target from ``orderset_cls.get_fields()``.
#   - build each input class through ``orders.inputs.build_input_class`` and
#     ``orders.inputs._build_input_fields``.
#   - raise ``ConfigurationError`` when two distinct ``OrderSet`` classes claim
#     the same ``<Name>InputType``.
#   - do not implement Layer 6 / dynamic ``OrderSet`` generation in this card.
