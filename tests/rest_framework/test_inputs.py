# TODO(spec-039 Slice 1): Add package tests for serializer input materialization
# and shape identity.
# Pseudo cases:
#   - create and partial inputs derive from schema-time serializer fields;
#   - read-only and hidden fields are dropped;
#   - `optional_fields` makes create fields optional and rejects bare strings;
#   - serializer-only fields remain included;
#   - request-dependent serializer kwargs fail without a schema hook;
#   - context-dependent fields fail during materialization;
#   - schema hooks can supply a stable request-independent shape;
#   - shape identity differs by requiredness, source, and conversion kind;
#   - identical shapes dedupe while same-name distinct shapes raise;
#   - create-required guards run per declaration before cache lookup.
#
# Boundary: schema/build-time invalid configurations stay here because a live
# `/graphql/` request cannot reach an unbuildable schema.
