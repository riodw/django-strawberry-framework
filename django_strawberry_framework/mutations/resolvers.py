"""Create, update, and delete resolver pipelines reserved by spec-036."""

# TODO(spec-036 Slice 3): implement sync and async mutation write pipelines.
# Pseudocode:
# - decode ``data`` and operation ``id`` arguments, distinguishing UNSET, None,
#   and concrete values for partial updates;
# - for update and delete, locate the row through the target type's
#   ``get_queryset`` plus any cascade-permission narrowing, returning a
#   not-found ``FieldError`` for hidden or missing rows;
# - build or mutate the model instance and call ``full_clean``; partial updates
#   exclude fields not provided by the PartialInput;
# - convert Django ValidationError, including validate_constraints
#   UniqueConstraint failures, into the shared FieldError envelope;
# - save or delete, mapping save-time IntegrityError races to the same envelope
#   as a best-effort fallback;
# - for create and update, re-fetch the written row by pk without the visibility
#   filter, then apply the optimizer for the response selection;
# - for delete, optimizer-load the response snapshot before deleting the row;
# - raise SyncMisuseError when a sync path receives an async get_queryset hook.
