# ruff: noqa: D100

# TODO(spec-039 Slice 1): Build serializer-derived input classes from a stable
# schema-time serializer field set.
# Pseudo flow:
#   - Guard DRF import, then create the serializer input namespace through
#     `make_input_namespace(...)` using this module path and `SerializerMutation`.
#   - Create the serializer shape cache through the shared cache helper.
#   - Represent shape identity with operation kind, ordered field specs, default
#     state, serializer field names, sources, conversion kinds, and optional fields.
#   - Build schema fields through `get_serializer_for_schema()` and translate
#     unstable `.fields` access into a `ConfigurationError`.
#   - Normalize `fields`/`exclude`, drop read-only and hidden fields, run the
#     create-required guard before cache lookup, and build both create and partial
#     inputs through `convert_serializer_field(...)` plus the unified field spec.
#   - Materialize generated classes as real module globals for `strawberry.lazy`.
#
# Required DRY contract:
#   - Use `utils.inputs.build_strawberry_input_class`.
#   - Use `utils.inputs.materialize_generated_input_class` through the namespace
#     helper; do not copy the mutation/form ledger by hand.
#   - Use `mutations.inputs._pascalize_token` until that helper is promoted.
