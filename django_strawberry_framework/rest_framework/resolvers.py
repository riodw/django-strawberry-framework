# ruff: noqa: D100

# TODO(spec-039 Slice 3): Implement the serializer runtime through the promoted
# shared write-pipeline skeleton, not a third hand-written orchestration.
# Pseudo flow:
#   - `resolve_serializer_mutation_sync(...)` calls `run_write_pipeline_sync(...)`
#     with the mutation class, info, input data, optional lookup id, and serializer
#     write-step callback.
#   - The serializer write step decodes input through the reverse map, builds
#     serializer kwargs through `get_serializer_kwargs(...)`, sets `partial` for
#     update operations, and always supplies request context.
#   - Invalid serializers return flattened `FieldError` leaves.
#   - Valid serializers call `save()` exactly once, capturing the returned object
#     for optimized refetch, while save-time validation/integrity exceptions pass
#     through the same field-error envelope.
#
# Security and coverage obligations:
#   - Locate -> authorize -> decode; relation decode never runs before write auth.
#   - Relation ids accept GlobalID or raw pk, are type checked, then visibility
#     checked through the related primary DjangoType.
#   - Upload values land in serializer `data`, not a form-style `files`.
#   - Consumer-reachable branches are covered live in products over `/graphql/`.
