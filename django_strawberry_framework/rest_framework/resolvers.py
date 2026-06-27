# ruff: noqa: D100

# TODO(spec-039 Slice 3): Implement the serializer runtime through the promoted
# shared write-pipeline skeleton, not a third hand-written orchestration.
# Pseudo flow:
#   - `resolve_serializer_mutation_sync(...)` calls `run_write_pipeline_sync(...)`
#     with the mutation class, info, input data, optional lookup id, and serializer
#     `decode_step` / `write_step` callbacks.
#   - The decode step runs only after authorization, maps GraphQL input names back
#     to declared serializer field names, and resolves relation targets through
#     the recorded effective GlobalID strategy, not live settings reads.
#   - The write step builds serializer kwargs through `get_serializer_kwargs(...)`,
#     merges request context, rejects `partial=False` on update or `partial=True`
#     on create, and injects framework-owned `partial=True` for updates.
#   - Invalid serializers return flattened `FieldError` leaves keyed to GraphQL
#     input names where a reverse-map entry exists.
#   - Valid serializers call `save()` exactly once, capturing the returned object
#     for optimized refetch. Save-time DRF `ValidationError`, Django
#     `ValidationError`, and `IntegrityError` are three separate envelope paths.
#
# Security and coverage obligations:
#   - Locate -> authorize -> decode; relation decode never runs before write auth.
#   - The generated relation field exposes one shape, but the shared decoder
#     helper accepts GlobalID or raw pk for non-live/package-only branches.
#   - Upload values land in serializer `data`, not a form-style `files`.
#   - Consumer-reachable branches are covered live in products over `/graphql/`.
