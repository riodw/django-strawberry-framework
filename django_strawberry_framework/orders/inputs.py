"""Planned order input namespace and direction enum."""

# TODO(spec-028-orders-0_0_8 Slice 1): Add the public ``Ordering`` enum.
# Pseudocode:
#   - define six members: ``ASC``, ``DESC``, ``ASC_NULLS_FIRST``,
#     ``ASC_NULLS_LAST``, ``DESC_NULLS_FIRST``, ``DESC_NULLS_LAST``.
#   - implement ``resolve(field_path)`` by returning Django ``F(field_path).asc``
#     or ``.desc`` with ``nulls_first=True`` / ``nulls_last=True`` only for the
#     qualified enum members; use ``None`` for the no-clause sentinel.
#
# TODO(spec-028-orders-0_0_8 Slice 2): Build and materialize Strawberry input
# classes in this module namespace.
# Pseudocode:
#   - set ``INPUTS_MODULE_PATH = "django_strawberry_framework.orders.inputs"``.
#   - derive input names through ``_input_type_name_for(OrderSet)`` delegating to
#     ``OrderSet.type_name_for()``.
#   - emit leaf fields as ``Ordering | None``.
#   - emit ``RelatedOrder`` fields as
#     ``Annotated["<Target>InputType", strawberry.lazy(INPUTS_MODULE_PATH)] | None``.
#   - track flat shorthand fields with a ``FieldSpec``-style map so
#     ``shelf__code`` exposes ``shelfCode`` but normalizes back to the ORM path.
#   - make ``materialize_input_class(name, input_cls)`` idempotent for the same
#     ``name -> input class`` pair and raise ``ConfigurationError`` for
#     collisions against a different class.
#
# TODO(spec-028-orders-0_0_8 Slice 3): Add ``clear_order_input_namespace`` with
# the parked-global lifecycle from Decision 9.
# Pseudocode:
#   - clear the materialization ledger and per-field provenance map.
#   - clear ``OrderArgumentsFactory.input_object_types`` and
#     ``OrderArgumentsFactory._type_orderset_registry``.
#   - reset each ``OrderSet`` subclass's direct binding/cache attributes:
#     ``_owner_definition``, ``_expanded_fields``, and ``_is_expanding_fields``.
#   - leave materialized module globals parked in ``orders.inputs.__dict__`` so
#     held ``strawberry.lazy(...)`` references keep resolving until the next
#     finalize pass replaces them.
