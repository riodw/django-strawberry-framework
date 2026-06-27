# ruff: noqa: D100

# TODO(spec-039 Slice 1): Build serializer-derived input classes from a stable
# schema-time serializer field set.
# Pseudo flow:
#   - Guard DRF import, then create the serializer input namespace through
#     `make_input_namespace(...)` using this module path and `SerializerMutation`.
#   - Create the serializer shape cache through the shared cache helper.
#   - Represent shape identity with operation kind, ordered field specs, default
#     state, GraphQL annotation, serializer field names, sources, conversion
#     kinds, and optional fields.
#   - Build schema fields through `get_serializer_for_schema()` and wrap the
#     `.fields` materialization step, not only construction; DRF builds fields
#     lazily, so request-shaped serializers fail at `.fields` access.
#   - Normalize `fields`/`exclude`, drop read-only and hidden fields, run the
#     create-required guard before cache lookup, and build both create and partial
#     inputs through `convert_serializer_field(...)` plus the unified field spec.
#   - Generate exactly one relation annotation per field: Relay `GlobalID` for a
#     Relay-shaped target, otherwise the target raw-pk scalar. The decoder helper
#     may accept both shapes, but a live GraphQL input exposes only one.
#   - Materialize generated classes as real module globals for `strawberry.lazy`.
#
# Required DRY contract:
#   - Use `utils.inputs.build_strawberry_input_class`.
#   - Use `utils.inputs.materialize_generated_input_class` through the namespace
#     helper; do not copy the mutation/form ledger by hand.
#   - Use `mutations.inputs._pascalize_token` until that helper is promoted.
