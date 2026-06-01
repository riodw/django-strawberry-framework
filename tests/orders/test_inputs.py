"""Planned tests for order input adapters and lifecycle helpers."""

# TODO(spec-028-orders-0_0_8 Slice 2): Cover input conversion, materialization,
# helper annotation shape, and clear lifecycle.
# Pseudocode:
#   - assert ``convert_order_field_to_input_annotation`` always returns
#     ``Ordering | None`` for scalar, choice, FK, PK, and BigInteger fields.
#   - assert ``normalize_input_value`` walks nested inputs into flat
#     ``(field_path, Ordering)`` pairs, including flat shorthand paths.
#   - assert ``materialize_input_class`` writes module globals and is idempotent
#     for the same ``name -> class`` pair.
#   - assert collisions against a different class raise ``ConfigurationError``.
#   - assert ``clear_order_input_namespace`` clears ledgers / factory caches /
#     orderset binding state while leaving materialized module globals parked.
#   - assert ``order_input_type`` returns the element ``Annotated[...]`` forward
#     reference and repeated calls keep one helper-ledger entry.
#   - assert resolver annotation ``list[order_input_type(MyOrder)] | None`` emits
#     GraphQL SDL ``orderBy: [MyOrderInputType!]``.
#   - assert each ``Ordering`` member renders the expected Django ``OrderBy`` SQL.
