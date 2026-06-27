# ruff: noqa: D100

# TODO(spec-039 Slice 2): Implement `SerializerMutation` as the ModelSerializer
# flavor of `DjangoMutation`.
# Pseudo flow:
#   - Guard DRF import, then define `SerializerMutation` as an abstract
#     `DjangoMutation` subclass.
#   - Resolve the backing model from `serializer_class.Meta.model`.
#   - Validate Meta by rejecting unknown keys, requiring a `ModelSerializer` with
#     a concrete model, accepting only shared non-delete operations, normalizing
#     `fields`/`exclude` and `optional_fields`, and validating permission classes.
#   - Reuse `_ValidatedMutationMeta` rather than introducing a parallel serializer
#     metadata carrier.
#   - Delegate input naming/building to `rest_framework.inputs` and resolver entry
#     points to `rest_framework.resolvers`.
#
# Required DRY contract:
#   - Do not create `bind_serializer_mutations`; this rides `bind_mutations()`.
#   - Do not create `_VALID_SERIALIZER_OPERATIONS`; import the shared non-delete
#     operation set.
#   - Do not fork `_cached_build_form_input`; use the promoted build/cache helpers.
